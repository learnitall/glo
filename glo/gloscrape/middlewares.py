#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Middlewares for our scrapy spiders."""
import os
import logging
import random
import shutil
import shlex
import subprocess
import uuid
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
        self.vpn_tag = uuid.uuid4()
        self.user_agent = next(self.user_agents)

    @classmethod
    def from_crawler(cls, crawler):
        """Initiate middleware."""

        ua_file = os.path.abspath(crawler.settings.get("USER_AGENT_FILE"))
        vpn_file = os.path.abspath(crawler.settings.get("WS_VPN_LIST_FILE"))
        return cls(ua_file, vpn_file)

    @staticmethod
    def _get_line_generator(file_path):
        """Return generator that yields random lines from given file."""

        def get_rand_line():
            with open(file_path, "r") as f_obj:
                while True:
                    f_obj.seek(0, 2)
                    filesize = f_obj.tell()

                    random_line = random.randint(0, filesize)
                    f_obj.seek(random_line)
                    f_obj.readline()  # might be in middle of line
                    result = f_obj.readline()
                    if len(result) == 0:  # might have ended up at EOF
                        f_obj.seek(0)
                        result = f_obj.readline()
                    yield result.strip()

        return get_rand_line()

    def _windscribe_reconnect(self, retries=3):
        """Reconnect windscribe though the CLI."""

        self.logger.debug(
            "Reconnecting to windscribe with %s retries", retries
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
            self.logger.debug(
                "Successfully reconnected to windscribe: %s", out
            )
            self.vpn_tag = uuid.uuid4()

        except (subprocess.CalledProcessError, ValueError) as exception:
            self.logger.warning(
                "Unable to reconnect to windscribe: %s", exception
            )
            if retries != 0:
                self.logger.warning("Retrying...")
                self._windscribe_reconnect(retries=retries - 1)
            else:
                raise RuntimeError(
                    f"Unable to reconnect to windscribe: {exception}"
                ) from exception

    # pylint: disable=unused-argument
    def process_request(self, request, spider):
        """Set user agent header and meta for current vpn."""
        request.headers.setdefault(b"User-Agent", self.user_agent)
        request.headers[b"User-Agent"] = self.user_agent
        request.meta["vpn-tag"] = self.vpn_tag

    # pylint: disable=unused-argument
    def process_response(self, request, response, spider):
        """On access denied, try to reconnect to windscribe."""

        if (
            response.css("title::text").get() == "Access Denied"
            or response.status == 504
            or response.status == 403
        ):
            if request.meta["vpn-tag"] == self.vpn_tag:
                self.logger.info("Got Access Denied for %s", request.url)
                self._windscribe_reconnect()
                self.user_agent = next(self.user_agents)
                self.logger.debug(
                    "Setting user-agent to '%s'", self.user_agent
                )

                request.headers.setdefault(b"User-Agent", self.user_agent)

            self.logger.info(
                "Retrying access denied with updated vpn for '%s'", request.url
            )
            request.headers[b"User-Agent"] = self.user_agent
            new_req = request.copy()
            new_req.meta["vpn-tag"] = self.vpn_tag
            return new_req

        return response
