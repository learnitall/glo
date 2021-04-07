#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for working with and representing nutrition information."""
import string
from typing import Set
from functools import reduce
import re
from sklearn.preprocessing import FunctionTransformer
from ._ureg import Q_


class ASCIIUnitParser:
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
    _r_unit = f'(?:{_r_digit})[\ \w]+'
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
