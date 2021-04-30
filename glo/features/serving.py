#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for working with and representing nutrition information."""
from typing import Callable, Union
import warnings
import pandas as pd
import numpy as np
from pint import UndefinedUnitError
from glo.units import (
    Q_,
    Q_class,
    simplified_div,
    BaseUnitParser,
    ASCIIUnitParser,
    ureg,
)
from glo.transform import PandasBaseTransform, filter_nan_wrap


def get_num_servings(
    weight: str,
    serving_size: str,
    div_func: Callable[[Q_class, Q_class], float] = simplified_div,
    unit_parser: BaseUnitParser = ASCIIUnitParser(),
) -> float:
    """
    Return number of servings based on weight and serving size.

    Will pass the weight and serving_size parameters to the given
    unit parser first. Will then try diffenent combinations of
    the pulled substrings until a successful result from the
    given division function.

    Parameters
    ----------
    weight: str
        string representing weight
    serving_size: str
        string representing serving size
    div_func: callable, optional
        This function is used to perform the division of the weight
        and serving size parameters. A custom one can be given if
        needed.
    unit_parser: instance of BaseUnitParser, optional
        UnitParser instance to use to parse weight and serving size
        parameters into set of possible unit substrings.

    Returns
    -------
    float
        Number of servings based on the given parameters.

    Raises
    ------
    ValueError
        If the number of servings cannot be determined from the
        given parameters.

    Examples
    --------
    >>> from glo.features.serving import get_num_servings
    >>> get_num_servings("15 ounces", "5 ounces")
    3.0
    >>> get_num_servings("5 bottles (25 ounces)", "1 bottle (5 ounces)")
    5.0

    See Also
    --------
    glo.features._ureg.simplified_div
    BaseUnitParser
    ASCIIUnitParser
    """

    weight_strs = unit_parser.find_unit_strs(weight)
    ss_strs = unit_parser.find_unit_strs(serving_size)
    for w_str in weight_strs:
        for s_str in ss_strs:
            try:
                w_qt, s_qt = Q_(w_str), Q_(s_str)
                return div_func(w_qt, s_qt)
            except (UndefinedUnitError, TypeError):
                pass

    raise ValueError(
        f"Unable to determine number of servings with weight {weight} and "
        f"servings {serving_size}"
    )


class PandasParseServing(PandasBaseTransform):
    """
    Add ``servings`` column to the dataset.

    Use the ``weight`` and ``servings`` columns to parse the number
    of servings per food item and create a new column named
    ``servings``.

    Parameters
    ----------
    parser: BaseUnitParser
        Set ``parser`` attribute. Defaults to
        ``glo.features.serving.ASCIIUnitParser()``.

    Attributes
    ----------
    parser: BaseUnitParser
        Passed to ``unit_parser`` of
        ``glo.features.serving.get_num_servings``.
    """

    def __init__(self, parser: BaseUnitParser = ASCIIUnitParser(), **kwargs):
        self.parser = parser
        super().__init__(**kwargs)

    @staticmethod
    def div_func(  # pylint: disable=invalid-name
        q1: Q_class, q2: Q_class
    ) -> float:
        """
        Return float of simplified division of quantities.

        This essentially wraps ``glo.units.simplified_div`` by
        performing some extra magic requied by the King Soopers
        dataset. For instance, sometimes the King Soopers dataset
        will incorrectly use "oz" instead of "floz", and this
        function will replace "oz" to "floz" when the other unit
        is a liquid volume.

        Parameters
        ----------
        q1: pint.Quantity instance
        q2: pint.Quantity instance

        Returns
        -------
        float

        Raises
        ------
        TypeError
            If the units of the given quantities cannot be simplified to a
            dimensionless value

        See Also
        --------
        glo.units.simplified_div
        """

        if q1.units == ureg.ounce and q2.units.is_compatible_with(
            ureg.fluid_ounce
        ):
            q1 = Q_(q1.magnitude, ureg.fluid_ounce)
        elif q2.units == ureg.ounce and q1.units.is_compatible_with(
            ureg.fluid_ounce
        ):
            q2 = Q_(q2.magnitude, ureg.fluid_ounce)

        return simplified_div(q1, q2)

    @filter_nan_wrap
    def transform_series(self, series: pd.Series) -> Union[pd.Series, float]:
        result = series.copy(deep=True)

        weight = series["weight"]
        serving_size = series["serving"]
        try:
            servings = get_num_servings(
                weight,
                serving_size,
                div_func=self.div_func,
                unit_parser=self.parser,
            )
        except ValueError as exception:
            warnings.warn(exception.args[0], RuntimeWarning)
            return np.nan

        result["servings"] = np.float64(servings)
        return result
