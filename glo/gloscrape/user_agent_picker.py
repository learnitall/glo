#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adapted from code by Neal Wong (ibprnd@gmail.com). Please see
https://github.com/rejoiceinhope/crawler-demo/tree/master/crawling-basic/scrapy_user_agents
"""
import random
import logging
import user_agents  # pylint: disable=import-error

logger = logging.getLogger(__name__)


def group_by_device_type(uas_list):
    """
    Group user agent by device type.

    Supported device types are: "desktop", "mobile", "tablet".
    """

    user_dict = {
        "desktop": {
            "chrome": dict(),
            "safari": dict(),
            "firefox": dict(),
            "opera": dict(),
            "ie": dict(),
        },
        "mobile": {
            "chrome": dict(),
            "safari": dict(),
            "firefox": dict(),
            "opera": dict(),
            "ie": dict(),
        },
        "tablet": {
            "chrome": dict(),
            "safari": dict(),
            "firefox": dict(),
            "opera": dict(),
            "ie": dict(),
        },
    }
    for user_agent in uas_list:
        parsed_ua = user_agents.parse(user_agent)
        os_family = parsed_ua.os.family

        if parsed_ua.is_mobile:
            device_dict = user_dict["mobile"]
        elif parsed_ua.is_tablet:
            device_dict = user_dict["tablet"]
        elif parsed_ua.is_pc:
            device_dict = user_dict["desktop"]
        else:
            logger.warning(
                "[UnsupportedDeviceType] Family: %s, Brand: %s, Model: %s",
                parsed_ua.device.family,
                parsed_ua.device.brand,
                parsed_ua.device.model,
            )
            continue

        raw_browser_family = parsed_ua.browser.family.lower()
        if (
            raw_browser_family.find("safari") != -1
            and raw_browser_family.find("chrome") == -1
        ):
            browser_dict = device_dict["safari"]
        elif raw_browser_family.find("chrome") != -1:
            browser_dict = device_dict["chrome"]
        elif raw_browser_family.find("firefox") != -1:
            browser_dict = device_dict["firefox"]
        elif (
            raw_browser_family.find("opera") != -1
            or raw_browser_family.find("opr") != -1
        ):
            browser_dict = device_dict["opera"]
        elif (
            raw_browser_family.find("msie") != -1
            or raw_browser_family.find("ie") != -1
        ):
            browser_dict = device_dict["ie"]
        else:
            logger.warning(
                "[UnsupportedBrowserType] Family: %s", parsed_ua.browser.family
            )
            continue

        if os_family in browser_dict:
            browser_dict[os_family].append(user_agent)
        else:
            browser_dict[os_family] = [user_agent]

    return user_dict


class UserAgentPicker:
    """Pick user agent by type."""

    # pylint: disable=too-few-public-methods

    # pylint: disable=too-many-arguments,too-many-locals
    def __init__(self, uas, ua_type, same_os_family, per_proxy, fallback):
        self.ua_type = ua_type
        self.same_os_family = same_os_family
        self.per_proxy = per_proxy
        self.fallback = fallback
        self.proxy2ua = {}

        ua_type = ua_type.split(".")
        uas_by_device = dict(group_by_device_type(uas))
        self.uas_by_device = uas_by_device
        device_type = ua_type.pop(0)
        if device_type not in uas_by_device:
            device_type = "desktop"

        try:
            browser_family = ua_type.pop()
            if (
                browser_family not in uas_by_device[device_type]
                and browser_family != "random"
            ):
                browser_family = "chrome"
        except IndexError:
            browser_family = "chrome"

        if same_os_family:
            uas_list = dict()
            if browser_family == "random":
                for all_browsers in uas_by_device[device_type].values():
                    for os_family, browsers in all_browsers.items():
                        if os_family in uas_list:
                            uas_list[os_family].extend(browsers)
                        else:
                            uas_list[os_family] = list(browsers)
            else:
                for os_family, browsers in uas_by_device[device_type][
                    browser_family
                ].items():
                    if os_family in uas_list:
                        uas_list[os_family].extend(browsers)
                    else:
                        uas_list[os_family] = list(browsers)

            max_uas = 0
            target_uas = []
            for same_os_uas in uas_list.values():
                count = len(same_os_uas)
                if count > max_uas:
                    max_uas = count
                    target_uas = same_os_uas
            self.uas_list = list(target_uas)
        else:
            uas_list = []
            if browser_family == "random":
                for all_browsers in uas_by_device[device_type].values():
                    for browsers in all_browsers.values():
                        uas_list.extend(browsers)
            else:
                for browsers in uas_by_device[device_type][
                    browser_family
                ].values():
                    uas_list.extend(browsers)
            self.uas_list = uas_list

    def get_ua(self, proxy=None):
        """Gets random UA based on the type setting (random, firefox…)"""
        if proxy and self.per_proxy and proxy in self.proxy2ua:
            return self.proxy2ua[proxy]

        if len(self.uas_list) <= 0:
            if self.fallback is None:
                raise RuntimeError("Error occurred during getting browser")

            logger.warning(
                'Error occurred during getting browser for type "%s", '
                "but was suppressed with fallback.",
                self.ua_type,
            )
            return self.fallback

        user_agent = random.choice(self.uas_list)
        if proxy and self.per_proxy:
            self.proxy2ua[proxy] = user_agent

        return user_agent
