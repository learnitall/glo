#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrapy items for collecting product data.
"""
from scrapy.item import Item, Field
from scrapy.loader import ItemLoader
from itemloaders.processors import Compose, Identity, TakeFirst


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
    # Additionally, if we get an empty string then replace
    # with None
    default_output_processor = Compose(
        TakeFirst(), lambda s: None if len(s) == 0 else s
    )
    # upc is given as "UPC: <code>"
    upc_in = Compose(TakeFirst(), lambda s: s.split(': ')[-1])
    # Sometimes we get keys with a value of unit zero
    # Want to remove these to save space
    nutrition_in = Compose(
        TakeFirst(),
        lambda d: {k: v for k, v in d.items() if not v.startswith('0')}
    )
    # expecting a list for this attribute
    indicators_out = Identity()
