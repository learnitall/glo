#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for working with and representing nutrition information."""
from typing import Callable
from pint import UndefinedUnitError
from glo.units import (
    Q_,
    Q_class,
    simplified_div,
    BaseUnitParser,
    ASCIIUnitParser,
)


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
