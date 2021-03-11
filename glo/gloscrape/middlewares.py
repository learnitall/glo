#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Middlewares for our scrapy spiders.

RandomUserAgentMiddleware adapted from code by
Neal Wong (ibprnd@gmail.com). Please see
https://github.com/rejoiceinhope/crawler-demo/tree/master/crawling-basic/scrapy_user_agents
"""
import os
import logging
from .user_agent_picker import UserAgentPicker


class LuminatiProxyManagerMiddleware:
    """Tells scrapy to use local Luminati Proxy Manager Instance."""

    def process_request(self, request, spider):
        request.meta["proxy"] = "http://localhost:24000"


class RandomUserAgentMiddleware(object):
    def __init__(self, crawler):
        self.logger = logging.getLogger(__name__)
        fallback = crawler.settings.get('RANDOM_UA_FALLBACK', None)
        per_proxy = crawler.settings.getbool('RANDOM_UA_PER_PROXY', False)
        ua_type = crawler.settings.get('RANDOM_UA_TYPE', 'desktop.chrome')
        same_os_family = crawler.settings.getbool('RANDOM_UA_SAME_OS_FAMILY', True)
        ua_file = crawler.settings.get('RANDOM_UA_FILE')
        if ua_file is None:
            cur_dir, _ = os.path.split(__file__)
            ua_file = os.path.join(cur_dir, 'default_uas.txt')
        else:
            ua_file = os.path.abspath(os.path.expanduser(ua_file))

        uas = []
        with open(ua_file) as ua_fh:
            for line in ua_fh:
                uas.append(line.strip())
        self.ua_picker = UserAgentPicker(uas, ua_type, same_os_family, per_proxy, fallback)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        proxy = request.meta.get('proxy')

        ua = self.ua_picker.get_ua(proxy)
        self.logger.debug('Assigned User-Agent %s', ua)
        request.headers.setdefault('User-Agent', ua)
