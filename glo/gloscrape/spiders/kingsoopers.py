#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrapy Spider for pulling products off of King Sooper's website.
"""
from scrapy.spiders import SitemapSpider
from ..items import *


class KingSooperSpider(SitemapSpider):
    """Scape King Sooper's website using their sitemaps."""

    name = 'kingsoopers'
    allowed_domains = ['kingsoopers.com']
    sitemap_urls = ['https://www.kingsoopers.com/product-details-sitemap.xml']

    def __parse_response(self, response):
        loader = KingSooperProductLoader(
            item=KingSooperProduct(), response=response
        )
        loader.add_value('url', response.url)
        loader.add_css('name', '.ProductDetails-header::text')
        loader.add_css('upc', '.ProductDetails-upc::text')
        loader.add_css('weight', '.ProductDetails-sellBy::text')
        loader.add_value(
            'price',
            dict(zip(
                response.css('label::attr(for)').getall(),
                response.css('.kds-Price::attr(value)').getall()
            ))
        )
        loader.add_css('allergens', '.NutritionIngredients-Allergens::text')
        loader.add_value(
            'indicators',
            response.css('.NutritionIndicators').xpath('./div/@title').getall()
        )
        loader.add_value(
            'serving',
            # returns ['serving size', '<serving size val']
            response.css('.NutritionLabel-ServingSize').xpath(
                './span/text()').getall()[-1],
        )
        loader.add_value('nutrition', dict(
            zip(
                response.css('.NutrientDetail-Title::text').getall(),
                response.css('.NutrientDetail-TitleAndAmount::text').getall()
            ))
        )

        item = loader.load_item()
        self.logger.debug(f"Parsed item: {item}")

        return item

    def parse(self, response, **kwargs):
        """Parse product page into a ``KingSooperProduct``."""

        url = response.url
        self.logger.debug(f"Got url {url}")
        if len(response.css('.Nutrition')) == 0:
            self.logger.debug(f"Skipping url (not food): {url}")
        else:
            self.logger.info(f"Parsing url {url}")

            yield self.__parse_response(response)
