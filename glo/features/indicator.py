#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for working with and representing food indicators."""
from typing import List
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from glo.transform import PandasBaseTransform, filter_nan_wrap


class PandasIndicatorNormalizer(PandasBaseTransform):
    """
    Normalize Indicator column of a pandas dataframe.

    Essentially just a wrapper around a LabelEncoder that allows
    for its usage with the ``indicators`` column in a pandas
    dataframe.

    We expect the ``indicators`` column to contain a list
    of string indicators on each row.
    """

    def __init__(self):
        super().__init__()
        self._labels = None
        self._encoder = LabelEncoder()

    def _inverse(self, indicator_norm_list: List[int]) -> List[str]:
        return self._encoder.inverse_transform(indicator_norm_list)

    def fit(self, dataframe: pd.DataFrame) -> "PandasIndicatorNormalizer":
        """
        Fit to given dataframe.

        Parameters
        ----------
        dataframe: pandas dataframe
            pandas dataframe to fit to.
        """

        self._labels = set()
        for indicators in dataframe["indicators"]:
            for indicator in indicators:
                self._labels.add(indicator.lower())
        self._encoder.fit(list(self._labels))
        return self

    @filter_nan_wrap
    def transform_series(self, series: pd.Series) -> pd.Series:
        result = series.copy(deep=True)
        if result.get("indicators", False):
            result["indicators"] = self._encoder.transform(
                list(map(str.lower, result["indicators"]))
            )
        return result
