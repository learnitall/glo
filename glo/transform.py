#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Classes for working with Transforms compatible with pytorch."""
from typing import Callable, List, Union
import functools
import numpy as np
import pandas as pd
from sklearn.preprocessing import FunctionTransformer


class BaseTransform(FunctionTransformer):
    """
    Base Class of a pytorch and sklearn compatible transform.

    To use, override the ``__call__`` method. This will be passed
    to the FunctionTransformer on initialization.

    Please note: the reason why ``fit`` on a ``BaseTransform``
    is set to an empty function that just returns ``None``, is that
    the defaunt ``fit`` method inherited from sklearn's
    ``FunctionTransformer``that doesn't might raise a TypeError due to
    numpy dtype validation. Since a lot of the transforms in glo are
    used for data cleaning, the fit has been overridden for convinence
    sake.
    """

    def __init__(self, **kwargs):
        kwargs["func"] = self.__call__
        kwargs["inverse_func"] = self._inverse
        super().__init__(**kwargs)

    def fit(self, sample):  # pylint: disable=unused-argument
        return self

    def _inverse(self, sample):  # pylint: disable=no-self-use
        return sample

    def __call__(self, sample):
        return sample


class PandasBaseTransform(BaseTransform):
    """
    Base class for building transforms on Pandas dataframes.

    To use, override the ``transform_series`` method, (which
    takes in a pandas Series, transforms it, then returns
    the transformed series), and/or the ``transform_dataframe``
    method, (which does the same except for DataFrames).
    The ``__call__`` method will call either the series
    transform method or the dataframe transform method,
    depending on the type of input that was given. This means
    that this transform can be used on both Pandas Series
    and DataFrames

    The ``transform_dataframe`` method by default will apply
    ``transform_series`` on each row in the given dataframe.
    """

    def transform_series(  # pylint: disable=no-self-use
        self, series: pd.Series
    ) -> pd.Series:
        """
        Transform the given series and return the result.

        By default, just returns the given Series.

        Parameters
        ----------
        series: pd.Series
            Pandas Series to transform.
        """

        return series

    def transform_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the given dataframe and return the result.

        By default this function will apply ``transform_series``
        on each row of the given dataframe.

        Parameters
        ----------
        df: pd.DataFrame
            Pandas DataFrame to transform.
        """

        return dataframe.apply(self.transform_series, axis=1)

    def __call__(
        self, sample: Union[pd.DataFrame, pd.Series]
    ) -> Union[pd.DataFrame, pd.Series]:

        if isinstance(sample, pd.DataFrame):
            return self.transform_dataframe(sample)
        return self.transform_series(sample)


class TransformCompose(BaseTransform):
    """
    Chain more than one ``BaseTransform`` together.

    Implementation of the same class from the torch vision library.

    Parameters
    ----------
    transforms: list of BaseTransforms
        List of transforms to chain together. Sets ``transforms``
        attribute.

    Attributes
    ----------
    tranforms: list of BaseTransforms.

    Examples
    --------
    >>> from glo.transform import TransformCompose
    >>> add_five = lambda a: a + 5
    >>> mult_five = lambda a: a * 5
    >>> tc = TransformCompose([add_five, mult_five, add_five])
    >>> tc(5)
    55
    >>> add_five(mult_five(add_five(5)))
    55
    """

    def __init__(self, transforms: List[BaseTransform], **kwargs):
        super().__init__(**kwargs)
        self.transforms = transforms

    def __call__(self, sample):
        return functools.reduce(
            lambda output, t_func: t_func(output), self.transforms, sample
        )


def filter_nan_wrap(
    func: Callable[
        [BaseTransform, Union[pd.Series, float]], Union[pd.Series, float]
    ]
) -> Callable[
    [BaseTransform, Union[pd.Series, float]], Union[pd.Series, float]
]:
    """
    Wrapper for transforms to only call transform if input is ``np.nan``.

    This funtion is meant to wrap the ``__call__`` method of
    subclasses for ``BaseTransform``. It could very well be
    rewritten as a metaclass, however, this option works too and may
    be more useful in the future.

    Parameters
    ----------
    func: callable
        Given function to wrap

    Returns
    -------
    callable
        If given sample is ``np.nan``, then will return sample.
        Otherwise, call the wrapped function.
    """

    def wrapped(
        self: BaseTransform, sample: Union[pd.Series, float]
    ) -> Union[pd.Series, float]:
        if sample.isna().values.all(axis=0):
            return sample
        return func(self, sample)

    return wrapped


class PandasFindMissing(PandasBaseTransform):
    """
    Set each column to ``np.nan`` if missing critical information.

    Parameters
    ----------
    expected_columns: dict
        Expected column names for keys, their expected types as
        values. If the column name is missing, or if one of the
        expected types is incorrect, then return ``np.nan``.
    fill_nan: bool
        If True, then if any of the expected columns are ``np.nan``, then
        transform the entire series to ``np.nan``.

    Attributes
    ----------
    expected_columns: dict
        Stores the given parameter ``expected_columns``.
    fill_nan: dict
        Stores the given parameter ``fill_nan``.
    missing_count: dict
        Keys are the columns from expected_columns, values are the
        number of columns that were deemed invalid.
    """

    def __init__(
        self, expected_columns: dict, fill_nan: bool = True, **kwargs
    ):
        self.expected_columns = expected_columns
        self.fill_nan = fill_nan
        self.missing_count = dict()
        super().__init__(**kwargs)

    @filter_nan_wrap
    def transform_series(self, series: pd.Series) -> Union[pd.Series, float]:
        for key, value in self.expected_columns.items():
            samp_val = series.get(key, None)
            if (
                samp_val is None
                or (self.fill_nan and samp_val is np.nan)
                or not isinstance(samp_val, value)
            ):
                self.missing_count[key] = self.missing_count.get(key, 0) + 1
                return np.nan

        return series
