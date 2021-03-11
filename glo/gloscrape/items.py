#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrapy items for collecting product data.
"""
from scrapy.item import Item, Field
from scrapy.loader import ItemLoader
from itemloaders.processors import Compose, TakeFirst


class KingSooperProduct(Item):
    """Item scraped on King Sooper's website."""

    name = Field()
    upc = Field()
    url = Field()
    weight = Field()
    price = Field()
    allergens = Field()
    indicators = Field()
    nutrition = Field()
    serving = Field()


class KingSooperProductLoader(ItemLoader):
    """Load a King Sooper Item from scrapy response."""

    # Seems that the loader will do an implicit 'getall', so
    # by default just take the first one it gets
    default_output_processor = TakeFirst()
    # upc is given as "UPC: <code>"
    upc_in = Compose(TakeFirst(), lambda s: s.split(': ')[-1])
