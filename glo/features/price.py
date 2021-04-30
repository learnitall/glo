#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tools for working with and representing price information."""
import pandas as pd
import numpy as np
from glo.transform import PandasBaseTransform, filter_nan_wrap


PICKUP = "PICKUP"
DELIVERY = "DELIVERY"
SHIP = "SHIP"
PRICE_METHODS = {PICKUP, DELIVERY, SHIP}


class PandasSetPriceMethod(PandasBaseTransform):
    """
    Set ``price`` column of dataset to price of picked price method.

    King Soopers' website presents multiple methods for obtaining
    their products, with each method having a potentially different
    price. The scrapy spider will pull each of these and create a
    dictionary which maps the method to the associated price. This
    transform lets us pick which price to use. It may be applicable
    to other online shopping websites as well.

    If the given method cannot be found for the item, then ``np.nan``
    is used instead.

    Parameters
    ----------
    method: str
        The method whose price should be set in the ``price`` column.
        Should be one of the strings in ``PRICE_METHODS``. Defaults
        to ``PICKUP``.

    Attributes
    ----------
    method: str, optional
        Set to the given method parameter.

    Raises
    ------
    ValueError
        If the given method is not in ``PRICE_METHODS``
    """

    def __init__(self, method: str = PICKUP, **kwargs):
        if method not in PRICE_METHODS:
            raise ValueError(
                f"Expected method to be one of {list(PRICE_METHODS)}, "
                f"instead got: {method}"
            )

        self.method = method
        super().__init__(**kwargs)

    @filter_nan_wrap
    def transform_series(self, series: pd.Series) -> pd.Series:
        result = series.copy(deep=True)
        result["price"] = np.float64(series["price"].get(self.method, np.nan))
        return result
