#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrapy Spider for pulling products off of King Sooper's website.
"""
import os
from twisted.internet.error import ConnectionRefusedError
from scrapy.spiders import Spider
from scrapy.http import Request
from ..items import KingSooperProductLoader, KingSooperProduct


class KingSooperSpider(Spider):
    """
    Scape King Sooper's website using their sitemaps.

    King Soopers has some really good software for blocking requests.
    Requires Splash for JS rendering, a good VPN, and some curl magic.
    """

    name = "kingsoopers"
    allowed_domains = ["kingsoopers.com"]
    user_agent = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) "
        "AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9"
    )
    splash_args = {
        "args": {"images": 0, "wait": 2, "timeout": 30},
        "endpoint": "render.html",
    }

    def start_requests(self):
        """
        Pull URLs from sitemap file.

        King Soopers has quite the intense WAF, which means that we
        need to use splash for JS rendering. Splash unfortunately is
        having trouble reaching the sitemaps for King Soopers. Our
        approach is to therefor download the sitemaps ahead of time,
        (which is nice since now they are cached and stored on disk
        rather than memory), then manually go through and start our
        requests.

        Expects the argument ``kssm`` to be set from the command-line
        """

        sitemap_file = getattr(self, "kssm", None)  # set from cli
        if sitemap_file is None:
            raise ValueError("Need kssm argument to be set to sitemap file.")
        with open(os.path.abspath(sitemap_file), "r") as smfile:
            while True:
                # strip whitespace and then loc tags
                line = (
                    smfile.readline().strip().lstrip("<loc>").rstrip("</loc>")
                )
                if not line:
                    break
                elif line.startswith("https"):
                    yield Request(line, self.parse)

    def __parse_response(self, response):
        loader = KingSooperProductLoader(
            item=KingSooperProduct(), response=response
        )
        loader.add_css("url", 'link[rel="canonical"]::attr(href)')
        loader.add_css("name", ".ProductDetails-header::text")
        loader.add_css("upc", ".ProductDetails-upc::text")
        loader.add_css("weight", ".ProductDetails-sellBy::text")
        loader.add_value(
            "price",
            dict(
                zip(
                    response.css("label::attr(for)").getall(),
                    response.css(".kds-Price::attr(value)").getall(),
                )
            ),
        )
        loader.add_css("allergens", ".NutritionIngredients-Allergens::text")
        loader.add_value(
            "indicators",
            response.css(".NutritionIndicators")
            .xpath("./div/@title")
            .getall(),
        )
        loader.add_value(
            "serving",
            # returns ['serving size', '<serving size val']
            response.css(".NutritionLabel-ServingSize")
            .xpath("./span[2]/text()")
            .getall(),
        )
        loader.add_value(
            "nutrition",
            dict(
                zip(
                    response.css(".NutrientDetail-Title::text").getall(),
                    response.css(
                        ".NutrientDetail-TitleAndAmount::text"
                    ).getall(),
                )
            ),
        )

        item = loader.load_item()
        self.logger.debug(f"Parsed item: {item}")

        return item

    def parse(self, response, **kwargs):
        """Parse product page into a ``KingSooperProduct``."""

        if response.css("title::text").get() == "Access Denied":
            raise ConnectionRefusedError("Access Denied")
        una = response.css(".kds-Heading--xl::text").get()
        nut = response.css(".Nutrition").get()
        # use request url to ensure we get the right one
        # sometimes splash returns things out of order
        url = response.request.url
        if una is None or (una is not None and "unavailable" in una):
            self.logger.debug(f"Skipping url (unavailable): {url}")
            yield None
        elif nut is None or (nut is not None and len(nut) == 0):
            self.logger.debug(f"Skipping url (no nutrition info): {url}")
            yield None
        else:
            self.logger.info(f"Parsing url {url}")
            yield self.__parse_response(response)
