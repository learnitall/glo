#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Middlewares for our scrapy spiders."""
import os
import logging
import random
import shutil
import shlex
import subprocess
from scrapy import signals


class SplashRequestMiddleware:
    """Filter all requests to go through splash."""

    def __init__(self, splash_args=None):
        self.splash_args = splash_args

    @classmethod
    def from_crawler(cls, crawler):
        """Initiate middleware."""

        mid = cls(crawler.settings.get("SPLASH_ARGS"))
        crawler.signals.connect(
            mid.spider_opened, signal=signals.spider_opened
        )
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


class WindscribeMiddleware:
    """
    Reconnect Windscribe VPN on access denied returned in html.

    Assumes Windscribe is already installed, configured, and
    running.
    """

    logger = logging.getLogger(__name__).getChild("Windscribe")

    def __init__(self, ua_file: str, vpn_file: str):
        self.user_agents = self._get_line_generator(ua_file)
        self.vpns = self._get_line_generator(vpn_file)
        self.user_agent = next(self.user_agents)

    @classmethod
    def from_crawler(cls, crawler):
        """Initiate middleware."""

        ua_file = os.path.abspath(crawler.settings.get("USER_AGENT_FILE"))
        vpn_file = os.path.abspath(crawler.settings.get("WS_VPN_LIST_FILE"))
        return cls(ua_file, vpn_file)

    @staticmethod
    def _get_line_generator(file_path):
        """
        Return generator that yields random lines from given file.

        Follows the following: http://metadatascience.com/2014/02/27/random-sampling-from-very-large-files/
        (under algorithm 3).
        """

        def get_rand_line():
            with open(file_path, "r") as fp:
                while True:
                    fp.seek(0, 2)
                    filesize = fp.tell()

                    random_line = random.randint(0, filesize)
                    fp.seek(random_line)
                    fp.readline()  # might be in middle of line
                    result = fp.readline()
                    if len(result) == 0:  # might have ended up at EOF
                        fp.seek(0)
                        result = fp.readline()
                    yield result.strip()

        return get_rand_line()

    def _windscribe_reconnect(self, retries=3):
        """Reconnect windscribe though the CLI."""

        self.logger.debug(
            "Reconnecting to windscribe with %s retries", retries,
        )

        try:
            vpn = next(self.vpns)
            cmd = shlex.split(f"{shutil.which('windscribe')} connect '{vpn}'")
            self.logger.debug(f"Executing {cmd}")
            result = subprocess.run(cmd, capture_output=True, check=True)
            # Expecting last two lines of output to be:
            # connected to <location>
            # your ip changed from <ip> to <ip>
            res_stdout = result.stdout.decode("latin-1").strip()
            if ("Connected to" not in res_stdout) and (
                "Your IP changed from" not in res_stdout
            ):
                raise ValueError(f"Unexpected output {res_stdout}")
            out = "{} ({})".format(*res_stdout.split("\n")[-2:])
            self.logger.debug("Successfully reconnected to windscribe: %s", out)

        except (subprocess.CalledProcessError, ValueError) as e:
            self.logger.warning("Unable to reconnect to windscribe: %s", e)
            if retries != 0:
                self.logger.warning("Retrying...")
                self._windscribe_reconnect(retries=retries - 1)
            else:
                raise ValueError("Unable to reconnect to windscribe: %s", e)

    def process_request(self, request, spider):
        """Set user agent header."""
        request.headers.setdefault(b"User-Agent", self.user_agent)

    def process_response(self, request, response, spider):
        """On access denied, try to reconnect to windscribe."""

        if response.css("title::text").get() == "Access Denied" \
                or response.status == 504 \
                or response.status == 403:
            self.logger.info("Got Access Denied for %s", request.url)
            self._windscribe_reconnect()
            self.user_agent = next(self.user_agents)
            self.logger.debug("Setting user-agent to '%s'", self.user_agent)
            request.headers.setdefault(b"User-Agent", self.user_agent)
            return response.replace(status=403)

        return response
