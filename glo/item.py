#!/bin/env python3
# -*- coding: utf-8 -*-
"""Tools for working with and representing purchasable items."""
from typing import Mapping, Union


class Item:
    """
    Generic item a user can purchase at a store.

    Parameters
    ----------
    name: str
    upc: str, optional
        No validity checks are performed on this parameter in
        order to support multiple upc standards.
    price: float, optional
        Not designated with specific currency, such as USD, in
        order to support multiple currencies.

    Attributes
    ----------
    name: str
        Item's string name. May be human-readable or id-like.
    upc: str
        Universal Product Code for the item. If not given, will
        default to ``None``.
    price: float
        Item cost. If not given, will default to ``None``.

    Methods
    -------
    as_dict:
        Return dictionary representation of Item instance.
        See method docstring below.

    Examples
    --------
    >>> import glo
    >>> glo.Item('my_item')
    Product 'my_item'(None)@None
    >>> glo.Item('my_second_item', price=15.0)
    Product 'my_second_item'(None)@15.0
    >>> glo.Item('my_third_item', upc='000000000000', price=10.0)
    Product 'my_third_item'(000000000000)@10.0
    """

    __slots__ = ["name", "upc", "price"]

    def __init__(self, name: str, upc: str = None, price: float = None):
        """Item constructor."""

        self.name = name
        self.upc = upc
        self.price = price

    def __repr__(self):
        return f"Product '{self.name}'({self.upc})@{self.price}"

    def as_dict(self) -> Mapping[str, Union[str, float]]:
        """
        Return dictionary representation of the item.

        Dictionary contains documented attributes and their values.

        Examples
        --------
        >>> import glo
        >>> my_item = glo.Item('my_item', '1337000012340000', 0.50)
        >>> my_item.as_dict()
        {'name': 'my_item', 'upc': '1337000012340000', 'price': 0.5}
        """

        return {"name": self.name, "upc": self.upc, "price": self.price}
