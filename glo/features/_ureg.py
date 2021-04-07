#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Initialize unit registry from ``pint`` module."""
import pint

ureg = pint.UnitRegistry(system="SI")
Q_ = ureg.Quantity
_Q_class = Q_("1337 seconds").__class__


def simplified_div(q1: Q_, q2: Q_) -> float:  # pylint: disable=invalid-name
    """
    Return float of simplified division of quantities.

    Parameters
    ----------
    q1: pint.Quantity instance
    q2: pint.Quantity instance

    Returns
    -------
    float
        (q1 / q2).to_reduced_units()

    Raises
    ------
    TypeError
        If the units of the given quantities cannot be simplified to a
        dimensionless value
    """

    result = (q1 / q2).to_reduced_units()
    if result.dimensionless:
        return float(result.m)

    raise TypeError(
        f"Unable to simplify division of {q1} / {q2}. "
        f"Ended up with {result}."
    )
