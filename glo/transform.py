#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Classes for working with Transforms compatible with pytorch."""
from typing import List, Union
import functools
import pandas as pd
from sklearn.preprocessing import FunctionTransformer


class BaseTransform(FunctionTransformer):
    """
    Base Class of a pytorch and sklearn compatible transform.

    To use, override the ``__call__`` method. This will be passed
    to the FunctionTransformer on initialization.
    """

    def __init__(self, **kwargs):
        kwargs["func"] = self.__call__
        super().__init__(**kwargs)

    def __call__(self, sample):
        return sample


class PandasBaseTransfrom(BaseTransform):
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
