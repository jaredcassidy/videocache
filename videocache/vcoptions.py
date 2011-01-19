#!/usr/bin/env python
#
# (C) Copyright 2008-2011 Kulbir Saini <saini@saini.co.in>
#
# For more information on Videocache check http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from common import *
from error_codes import *

from vcconfig import VideocacheConfig

import logging
import logging.handlers
import os
import traceback
import urlparse

class VideocacheOptions:
    initialized = False
    halt = True

    def __init__(self, config_file = '/etc/videocache.conf', root = '/'):
        self.config_file = config_file
        self.root = root
        self.websites = ['youtube', 'metacafe', 'dailymotion', 'google', 'redtube', 'xtube', 'vimeo', 'wrzuta', 'youporn', 'soapbox', 'tube8', 'tvuol', 'bliptv', 'break']
        self.__class__.trace_logformat = '%(localtime)s %(process_id)s %(client_ip)s %(website_id)s %(code)s %(video_id)s\n%(message)s'
        self.format_map = { '%ts' : '%(timestamp)s', '%tu' : '%(timestamp_ms)s', '%tl' : '%(localtime)s', '%tg' : '%(gmt_time)s', '%p' : '%(process_id)s', '%s' : '%(levelname)s', '%i' : '%(client_ip)s', '%w' : '%(website_id)s', '%c' : '%(code)s', '%v' : '%(video_id)s', '%m' : '%(message)s', '%d' : '%(debug)s' }
        return self.initialize()

    def initialize(self):
        if self.__class__.initialized:
            return

        try:
            mainconf =  VideocacheConfig(self.config_file, self.root).read()
        except Exception, e:
            syslog_msg('Could not read configuration file! Debug: '  + traceback.format_exc().replace('\n', ''))
            return None

        try:
            # General Options
            self.__class__.enable_videocache = int(mainconf.enable_videocache)
            self.__class__.enable_videocache_cleaner = int(mainconf.enable_videocache_cleaner)
            self.__class__.video_lifetime = int(mainconf.video_lifetime)
            self.__class__.offline_mode = int(mainconf.offline_mode)
            self.__class__.videocache_user = mainconf.videocache_user
            self.__class__.videocache_group = mainconf.videocache_group
            self.__class__.max_cache_processes = int(mainconf.max_cache_processes)
            self.__class__.hit_threshold = int(mainconf.hit_threshold)
            self.__class__.max_video_size = int(mainconf.max_video_size) * 1024 * 1024
            self.__class__.min_video_size = int(mainconf.min_video_size) * 1024 * 1024

            # Filesystem
            base_dir_list = [dir.strip() for dir in mainconf.base_dir.split('|')]
            self.__class__.temp_dir = mainconf.temp_dir
            self.__class__.disk_avail_threshold = int(mainconf.disk_avail_threshold)

            # Logging
            self.__class__.logfile = os.path.join(mainconf.logdir, mainconf.logfile)
            self.__class__.max_logfile_size = int(mainconf.max_logfile_size) * 1024 * 1024
            self.__class__.max_logfile_backups = int(mainconf.max_logfile_backups)
            self.__class__.tracefile = os.path.join(mainconf.logdir, mainconf.tracefile)
            self.__class__.max_tracefile_size = int(mainconf.max_tracefile_size) * 1024 * 1024
            self.__class__.max_tracefile_backups = int(mainconf.max_tracefile_backups)
            self.__class__.logformat = mainconf.logformat
            self.__class__.timeformat = mainconf.timeformat
            self.__class__.scheduler_logfile = os.path.join(mainconf.logdir, mainconf.scheduler_logfile)
            self.__class__.max_scheduler_logfile_size = int(mainconf.max_scheduler_logfile_size) * 1024 * 1024
            self.__class__.max_scheduler_logfile_backups = int(mainconf.max_scheduler_logfile_backups)
            self.__class__.scheduler_pidfile = mainconf.scheduler_pidfile

            # Network
            self.__class__.cache_host = mainconf.cache_host
            self.__class__.rpc_host = mainconf.rpc_host
            self.__class__.rpc_port = int(mainconf.rpc_port)
            proxy = mainconf.proxy
            proxy_username = mainconf.proxy_username
            proxy_password = mainconf.proxy_password

            # Other
            self.__class__.pid = os.getpid()
        except Exception, e:
            syslog_msg('Could not load options from configuration file! Debug: '  + traceback.format_exc().replace('\n', ''))
            return None

        # Website specific options
        try:
            [ (setattr(self.__class__, 'enable_' + website_id + '_cache', int(eval('mainconf.enable_' + website_id + '_cache'))), setattr(self.__class__, website_id + '_cache_dir', eval('mainconf.' + website_id + '_cache_dir'))) for website_id in self.websites ]
        except Exception, e:
            syslog_msg('Could not set website specific options. Debug: ' + traceback.format_exc().replace('\n', ''))
            return None

        # Create a list of cache directories available
        try:
            base_dirs = {}
            for website_id in self.websites:
                base_dirs[website_id] = [os.path.join(dir, eval('self.__class__.' + website_id + '_cache_dir')) for dir in base_dir_list]
            self.__class__.base_dirs = base_dirs
        except Exception, e:
            syslog_msg('Could not build a list of cache directories. Debug: ' + traceback.format_exc().replace('\n', ''))
            return None

        try:
            self.__class__.cache_url = 'http://' + str(self.__class__.cache_host) + '/'
        except Exception, e:
            syslog_msg('Could not generate Cache URL for serving videos from cache. Debug: ' + traceback.format_exc().replace('\n', ''))
            return None

        try:
            self.__class__.proxy = None
            if proxy:
                if proxy_username and proxy_password:
                    proxy_parts = urlparse.urlsplit(proxy)
                    self.__class__.proxy = '%s://%s:%s@%s/' % (proxy_parts[0], proxy_username, proxy_password, proxy_parts[1])
                else:
                    self.__class__.proxy = proxy
        except Exception, e:
            syslog_msg('Could not set proxy for caching videos. Debug: ' + traceback.format_exc().replace('\n', ''))
            return None

        # HTTP Headers for caching videos
        self.__class__.redirect_code = '302'
        self.__class__.std_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
            'Accept-Language': 'en-us,en;q=0.5',
        }

        self.__class__.initialized = True
        self.__class__.halt = False

    def set_loggers(self):
        # Set loggers
        try:
            for key in self.format_map:
                self.__class__.logformat = self.__class__.logformat.replace(key, self.format_map[key])
            # Main Log file
            self.__class__.vc_logger = logging.Logger('VideocacheLog')
            self.__class__.vc_logger.setLevel(logging.DEBUG)
            vc_log_handler = logging.handlers.RotatingFileHandler(self.__class__.logfile, mode = 'a', maxBytes = self.__class__.max_logfile_size, backupCount = self.__class__.max_logfile_backups)
            self.__class__.vc_logger.addHandler(vc_log_handler)

            # Scheduler Log file
            self.__class__.vcs_logger = logging.Logger('VideocacheLog')
            self.__class__.vcs_logger.setLevel(logging.DEBUG)
            vcs_log_handler = logging.handlers.RotatingFileHandler(self.__class__.scheduler_logfile, mode = 'a', maxBytes = self.__class__.max_scheduler_logfile_size, backupCount = self.__class__.max_scheduler_logfile_backups)
            self.__class__.vcs_logger.addHandler(vcs_log_handler)

            # Trace log
            self.__class__.trace_logger = logging.Logger('VideocacheTraceLog')
            self.__class__.trace_logger.setLevel(logging.DEBUG)
            trace_log_handler = logging.handlers.RotatingFileHandler(self.__class__.tracefile, mode = 'a', maxBytes = self.__class__.max_tracefile_size, backupCount = self.__class__.max_tracefile_backups)
            self.__class__.trace_logger.addHandler(trace_log_handler)
        except Exception, e:
            syslog_msg('Could not set logging! Debug: '  + traceback.format_exc().replace('\n', ''))
            return None
        return True

    def reset(self):
        self.__class__.initialized = False
        self.initialize()

