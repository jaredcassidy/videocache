#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import re
import urllib
import urlparse

VALIDATE_SLUTLOAD_DOMAIN_REGEX1 = re.compile('\.slutload-media\.com')
VALIDATE_SLUTLOAD_DOMAIN_REGEX2 = re.compile('(.*)\/[a-zA-Z0-9_.-]+\.flv')

def check_slutload_video(o, url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'slutload', None, '', True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if VALIDATE_SLUTLOAD_DOMAIN_REGEX1.search(host) and VALIDATE_SLUTLOAD_DOMAIN_REGEX2.search(path) and path.find('.flv') > -1:
        try:
            video_id = urllib.quote(path.strip('/').split('/')[-1])
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

