#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Middlewares for our scrapy spiders."""
from scrapy import signals


class SplashRequestMiddleware:
    """Filter all requests to go through splash."""

    def __init__(self, splash_args=None):
        self.splash_args = splash_args

    @classmethod
    def from_crawler(cls, crawler):
        """Initiate middleware."""

        mid = cls(crawler.settings.get("SPLASH_ARGS"))
        crawler.signals.connect(mid.spider_opened, signal=signals.spider_opened)
        return mid

    def spider_opened(self, spider):
        """Get splash args from spider."""

        self.splash_args = getattr(spider, "splash_args", self.splash_args)

    def process_request(self, request, spider):
        """Add splash args to request."""

        if self.splash_args and not request.meta.get("splash", False):
            spider.logger.debug("Crawling %s", request.url)
            request.meta["splash"] = self.splash_args
            request.meta["splash"]["args"]["url"] = request.url
