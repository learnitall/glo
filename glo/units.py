#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Initialize unit registry from ``pint`` module."""
import pint
from abc import ABC, abstractmethod

ureg = pint.UnitRegistry(system="SI")
Q_ = ureg.Quantity
Q_class = Q_("1337 seconds").__class__


def simplified_div(
    q1: Q_class, q2: Q_class
) -> float:  # pylint: disable=invalid-name
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


class BaseQuantityParser(ABC):
    """
    Abstract Base Class for a QuantityParser.

    A QuantityParser class implements the ``get_quantity`` method,
    which takes in a string and returns a pint Quantity. This is an
    opportunity for the quantity strings to be filtered as needed
    before being parsed by pint.
    """

    @abstractmethod
    def get_quantity(self, s_in: str) -> Q_class:
        """
        Return pint Quantity for given input string.

        Parameters
        ----------
        s_in: str
            Input string to turn into a quantity
        """
