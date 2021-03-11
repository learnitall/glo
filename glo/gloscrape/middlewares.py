#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Custom Middlewares for our scrapy spiders."""


class LuminatiProxyManagerMiddleware:
    """Tells scrapy to use local Luminati Proxy Manager Instance."""

    def process_request(self, request, spider):
        request.meta["proxy"] = "http://localhost:24000"
