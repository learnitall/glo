#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for working with and representing nutrition information."""
from abc import ABC, abstractmethod
import string
from typing import Callable, Set
from functools import reduce
import re
from pint import UndefinedUnitError
from sklearn.preprocessing import FunctionTransformer
from ._ureg import Q_, simplified_div


class BaseUnitParser(ABC):
    """
    ABC of a UnitParser class.

    A UnitParser class implements the ``find_unit_strs`` method,
    which takes in a string and returns a set of substrings
    that define a quantity with units.
    """

    @abstractmethod
    def find_unit_strs(self, s: str) -> Set[str]:
        pass


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

    _r_digit = r'\d+\/{1}\d+|\d+\.{1}\d+|\d+'
    _r_unit = fr'(?:{_r_digit})[\ a-zA-Z]+'
    _printable = set(string.printable)

    def prep_str(self, s: str) -> str:
        """
        Takes in a string and prepares it for parsing.

        In this method we convert the string to all lowercase and
        remove any characters that aren't supported by the ASCII
        character set.

        Parameters
        ----------
        s: str
            Input string to prep.

        Returns
        -------
        str
            Prepped version of the input ``s``.

        Examples
        --------
        >>> from glo.features.serving import ASCIIUnitParser
        >>> aup = ASCIIUnitParser()
        >>> aup.prep_str("25 Ounces")
        25 ounces
        >>> aup.prep_str("some\x00string. with\x15 funny characters")
        somestring. with funny characters
        >>> aup.prep_str("    some string with whitespace   ")
        some string with whitespace
        """

        as_ascii = ''.join(filter(lambda x: x in self._printable, s))
        return as_ascii.strip().lower()

    def find_unit_strs(self, s: str) -> Set[str]:
        """
        Get set of possible unit substrings from input string.

        Parameters
        ----------
        s: str
            Input string to search through

        Returns
        -------
        set of str
            Set of possible unit substrings in input ``s``.

        Examples
        --------
        >>> from glo.features.serving import ASCIIUnitParser
        >>> aup = ASCIIUnitParser()
        >>> aup.find_unit_strs("25 ounces")
        {'25 ounces'}
        >>> aup.find_unit_strs("25 OUNCES")
        {'25 ounces'}
        >>> aup.find_unit_strs("12.5 cans / 12 fl oz")
        {'12.5 cans', '12 fl oz'}
        >>> aup.find_unit_strs("Serving size is 15 gal (1/3 jug)")
        {'15 gal', '1/3 jug'}
        """

        s = self.prep_str(s)
        matches = re.findall(f"({self._r_unit})", s)
        return set([m.strip() for m in matches])


def get_num_servings(
        weight: str, serving_size: str,
        div_func: Callable[[Q_, Q_], float]=simplified_div,
        unit_parser: BaseUnitParser=ASCIIUnitParser()) -> float:
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
    3
    >>> get_num_servings("5 bottles (25 ounces)", "1 bottle (5 ounces)")
    5

    See Also
    --------
    glo.features._ureg.simplified_div
    BaseUnitParser
    ASCIIUnitParser
    """

    weight_strs = unit_parser.find_unit_strs(weight)
    ss_strs = unit_parser.find_unit_strs(serving_size)
    for ws in weight_strs:
        for ss in ss_strs:
            try:
                wq, sq = Q_(ws), Q_(ss)
                return div_func(wq, sq)
            except (UndefinedUnitError, TypeError):
                pass

    raise ValueError(
        f"Unable to determine number of servings with weight {weight} and "
        f"servings {serving_size}"
    )
