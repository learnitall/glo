#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrapy Spider for pulling products off of King Sooper's website.
"""
from scrapy.spiders import SitemapSpider
from ..items import KingSooperProductLoader, KingSooperProduct

KS_SPLASH_ARGS = {
    "args": {
        "images": 0,
        "allowed_domains": "kingsoopers.com",
        "wait": 10,
        "timeout": 30
    },
    "endpoint": "render.html"
}


class KingSooperSpider(SitemapSpider):
    """Scape King Sooper's website using their sitemaps."""

    name = "kingsoopers"
    allowed_domains = ["kingsoopers.com"]
    sitemap_urls = ["https://www.kingsoopers.com/product-details-sitemap.xml"]
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) " \
                 "AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9"

    def __parse_response(self, response):
        loader = KingSooperProductLoader(
            item=KingSooperProduct(), response=response
        )
        loader.add_value("url", response.url)
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

    def start_requests(self):
        """Kick off spider by adding splash integration."""
        requests = list(super(KingSooperSpider, self).start_requests())
        for r in requests:
            r["meta"]["splash"] = KS_SPLASH_ARGS

    def parse(self, response, **kwargs):
        """Parse product page into a ``KingSooperProduct``."""

        url = response.url
        self.logger.debug(f"Got url {url}")
        if len(response.css(".Nutrition")) == 0:
            self.logger.debug(f"Skipping url (not food): {url}")
        else:
            self.logger.info(f"Parsing url {url}")

            yield self.__parse_response(response)
