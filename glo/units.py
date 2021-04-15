#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Initialize unit registry from ``pint`` module."""
from abc import ABC, abstractmethod
from typing import Set
import re
import pint
from glo.helpers import prep_ascii_str

ureg = pint.UnitRegistry(system="SI")
Q_ = ureg.Quantity
Q_class = Q_("1337 seconds").__class__


class BaseUnitParser(ABC):
    """
    ABC of a UnitParser class.

    A UnitParser class implements the ``find_unit_strs`` method,
    which takes in a string and returns a set of substrings
    that define a quantity with units.
    """

    @abstractmethod
    def find_unit_strs(self, s_in: str) -> Set[str]:
        """
        Get set of possible unit substrings from input string.

        Parameters
        ----------
        s_in: str
            Input string to search through

        Returns
        -------
        set of str
            Set of possible unit substrings in input ``s_in``.
        """


class ASCIIUnitParser(BaseUnitParser):
    """
    Parses Units from ASCII strings.

    Supports units in the following forms:
    * ``x/y units``
    * ``x.y units``
    * ``x units``
    where x and y are real numbers and units is a string
    representing the units of x and y.

    See Also
    --------
    pint.UnitRegistry.Quantity: Used in the background for unit
        parsing.
    string.printable: Used to filter string of any non-ascii
        characters
    """

    _r_digit = r"\d+\/{1}\d+|\d+\.{1}\d+|\d+"
    _r_unit = fr"(?:{_r_digit})[\ a-zA-Z]+"

    def find_unit_strs(self, s_in: str) -> Set[str]:
        """
        Get set of possible unit substrings from input string.

        Parameters
        ----------
        s_in: str
            Input string to search through

        Returns
        -------
        set of str
            Set of possible unit substrings in input ``s_in``.

        Examples
        --------
        >>> from glo.units import ASCIIUnitParser
        >>> aup = ASCIIUnitParser()
        >>> aup.find_unit_strs("25 ounces")
        {'25 ounces'}
        >>> aup.find_unit_strs("25 OUNCES")
        {'25 ounces'}
        >>> sorted(list(aup.find_unit_strs("12.5 cans / 12 fl oz")))
        ['12 fl oz', '12.5 cans']
        >>> sorted(list(
        ...     aup.find_unit_strs("Serving size is 15 gal (1/3 jug)")
        ... ))
        ...
        ['1/3 jug', '15 gal']
        """

        s_in = prep_ascii_str(s_in)
        matches = re.findall(f"({self._r_unit})", s_in)
        return {m.strip() for m in matches}


class UnitWithSpaceParser(ASCIIUnitParser):
    """
    Parses Units from ASCII Strings that have spaces in them.

    Some units are multiple words long. Pint handles these by
    adding a ``_`` in-between the words (i.e. ``light_year``).
    This parser will try to add the underscores into the given
    input strings.

    See Also
    --------
    glo.features.serving.ASCIIUnitParser
    """

    # add capture group on the words
    _r_unit_word = fr"(?:{ASCIIUnitParser._r_digit})([\ a-zA-Z]+)"

    def find_unit_strs(self, s_in: str) -> Set[str]:
        """
        Get set of possible unit substrings from input string.

        Parameters
        ----------
        s_in: str
            Input string to search through

        Returns
        -------
        set of str
            Set of possible unit substrings in input ``s_in``.

        Examples
        --------
        >>> from glo.units import UnitWithSpaceParser
        >>> up = UnitWithSpaceParser()
        >>> up.find_unit_strs("25 ounces")
        {'25 ounces'}
        >>> up.find_unit_strs("25 OUNCES")
        {'25 ounces'}
        >>> sorted(list(up.find_unit_strs("12.5 cans / 12 fl oz")))
        ['12 fl oz', '12 fl_oz', '12.5 cans']
        >>> sorted(list(
        ...     up.find_unit_strs("Serving size is 15 gal (1/3 jug)")
        ... ))
        ...
        ['1/3 jug', '15 gal']
        >>> sorted(list(
        ...     up.find_unit_strs("25 fluid ounces")
        ... ))
        ...
        ['25 fluid ounces', '25 fluid_ounces']
        """

        matches = set()
        for match in super().find_unit_strs(s_in):
            units = re.findall(self._r_unit_word, match)
            matches.add(match)
            for unit in units:
                unit = unit.strip()
                u_with_underscore = unit.strip().replace(" ", "_")
                matches.add(match.replace(unit, u_with_underscore))

        return matches


def simplified_div(  # pylint: disable=invalid-name
    q1: Q_class, q2: Q_class
) -> float:
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


def get_quantity_from_str(s_in: str, parser: BaseUnitParser) -> Set[Q_class]:
    """
    Parse the given input string and return set of pint Quantities

    Uses the given parser to find a set of all potential quantities
    and then tries to create a pint quantity from each. Returns only
    those that are successful.

    Parameters
    ----------
    s_in: str
        String to turn into a pint quantity
    parser: BaseUnitParser
        Unit Parser to find unit substrings within s_in

    Returns
    -------
    set
        Set of pint Quantities that could be found using the given
        input string.
    """

    unit_strs = parser.find_unit_strs(s_in)
    results = set()
    for u_str in unit_strs:
        try:
            results.add(Q_(u_str))
        except (pint.UndefinedUnitError, TypeError):
            pass

    return results
