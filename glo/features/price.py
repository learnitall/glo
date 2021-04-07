#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tools for working with and representing price information."""
from abc import ABC, abstractmethod
from typing import Dict


Price = NewType("Price", object)
PriceVal = NewType("PriceVal", Price)
PriceDesc = NewType("PriceDesc", int)
PriceDescDict = NewType("PriceWithDesc", Dict[Price, PriceDesc])


SHIPPED = PriceDesc(0)
PICKUP = PriceDesc(1)
DELIVERY = PriceDesc(2)


class Price(ABC):
    """
    Abstract Base Class for a Price class.

    A Price class is a method for accessing a
    """


class PriceParser(ABC):
    """
    Abstract Base Class for a PriceParser class.

    A PriceParser class is a grouping of methods for
    parsing the price for a food item. The goal of this class is
    to provide a base template definition for compatibility with
    other parts of glo.
    """

