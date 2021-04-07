#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for working with and representing nutrition information."""
from abc import ABC, abstractmethod
from typing import NewType
from functools import reduce
from _ureg import Q_


_r_digit = r'\d+\/{1}\d+|\d+\.{1}\d+|\d+'
_r_unit = f'(?:{_r_digit})[\ \w]+'
Serving = NewType("Servings", float)


class ServingParser(ABC):
    """
    Abstract Base Class for a ServingParser class.

    A ServingParser class is a grouping of methods for parsing
    the number of servings for a food item. The goal of this class is
    to provide a base template definition for compatibility with other
    parts of glo.

    Methods
    -------
    get_serving:
       Returns the number of servings for a given Food item.
    """

    @abstractmethod
    def get_servings(self, f: ):