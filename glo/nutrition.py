#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tools for working with and representing nutrition information."""
from typing import Any, Iterable, Mapping, Union
import collections
from pint.quantity import Quantity
from pint.unit import Unit
from ._ureg import Q_, ureg


# TODO: Add type hint for operator_func
def _operator_overload_wrap(operator_func):
    """
    Operator overload wrap to check type and name attribute.

    Check to make sure that when performing operations on a
    ``NutritionFact`` instance with an object denoted as ``other``,
    that ``other`` is of the proper type and that both objects
    have the same ``name``. Additionally this method will return
    the ``NutritionFact`` instance that the operation is being
     performed on to ensure that operations can be chained.

    If ``other`` is a ``float`` or an ``int``, then it will
    be passed to ``operator_func`` as a dimensionless quantity.

    Parameters
    ----------
    operator_func: callable
        Take in a ``NutritionFact`` instance and either another
        ``NutritionFact``, a ``pint.quantity.Quantity``, an int
        or a float, then perform some sort of operation on them
        (mainly add or sub).

    Raises
    ------
    TypeError
        If ``other`` is not a ``NutritionFact`` or a
        ``pint.quantity.Quantity``.
    ValueError
        If ``other`` does not have the same ``name`` as left-hand-side
        ``NutritionFact``.
    """

    def _wrapped(self, other):
        if isinstance(other, ureg.Quantity):
            ret_val = operator_func(self, other)
        elif isinstance(other, NutritionFact):
            if other.name != self.name:
                raise ValueError(
                    "Refusing to operator on two NutritionFacts with "
                    f"mismatch names: {self.name} != {other.name}"
                )
            ret_val = operator_func(self, other.quantity)
        elif isinstance(other, (float, int)):
            ret_val = operator_func(self, Q_(other, "dimensionless"))
        else:
            raise TypeError(
                f"Invalid type for operation with NutritionFact: {type(other)}"
            )
        return ret_val

    return _wrapped


class NutritionFact:
    """
    Representation of a basic nutrition fact (essentially a named unit).

    Parameters
    ----------
    name: str
        String name of the nutrition fact. Examples include "sodium",
        "fat", or "calories".
    quantity: pint.unit.Quantity
        Associated ``Quantity`` instance that determines value and units
        for the nutrition fact. If ``None`` is given, then quantity with
        unit ``dimensionless`` and magnitude ``0`` is created.

    Attributes
    ----------
    name: str
        See above parameter description.
    quantity: pint.unit.Quantity
        See above parameter description.
    amount:
        Property that allows for getting and setting the quantity
        attribute's value. Setting this attribute to ``val`` is
        equivalent to:

        ``self.quantity = glo.Q_(val, self.units)``

        Getting this attribute is equivalent to ``self.quantity.m``
    units: pint.unit.Unit
        Property that allows for getting and setting the quantity
        attribute's units. Setting this attribute to ``unit`` is
        equivalent to:

        ``self.quantity = self.quantity.to(self.amount, unit)``

        Getting this attribute is equivalent to ``self.quantity.units``.

    Examples
    --------
    >>> import glo
    >>> my_sodium = glo.NutritionFact("sodium", glo.Q_(250, "mg"))
    >>> my_sodium.name
    'sodium'
    >>> my_sodium.amount
    250
    >>> my_sodium.units
    <Unit('milligram')>
    >>> my_sodium.amount += 10; my_sodium.amount
    260
    >>> my_sodium.units = glo.ureg.grams; my_sodium.quantity
    <Quantity(0.26, 'gram')>
    """

    __slots__ = ["name", "quantity"]

    # TODO make name attribute readonly

    def __init__(self, name: str, quantity: Quantity = None):
        """NutritionFact constructor."""

        self.name = name

        if quantity is None:
            self.quantity = Q_(0, None)
        else:
            self.quantity = quantity

    @_operator_overload_wrap
    def __add__(self, quantity):
        return NutritionFact(self.name, self.quantity + quantity)

    @_operator_overload_wrap
    def __sub__(self, quantity):
        return NutritionFact(self.name, self.quantity - quantity)

    @_operator_overload_wrap
    def __mul__(self, other):
        return NutritionFact(self.name, self.quantity * other)

    @_operator_overload_wrap
    def __truediv__(self, other):
        return NutritionFact(self.name, self.quantity / other)

    @property
    def amount(self):
        """Amount of given nutrition fact this instance represents."""
        return self.quantity.m

    @amount.setter
    def amount(self, val: Any):
        self.quantity = Q_(val, self.units)

    @property
    def units(self):
        """`Pint` units for the amount of the nutrition fact."""
        return self.quantity.units

    @units.setter
    def units(self, units: Unit):
        self.quantity = self.quantity.to(units)


class NutritionSet(collections.UserDict):

    def __init__(self, *facts: NutritionFact):
        """NutritionSet constructor."""

        super().__init__(facts)

    def __getitem__(self, key) -> NutritionFact:
        try:
            return super().__getitem__(key)
        except KeyError:
            return NutritionFact(key, Q_(0, None))

    def __setitem__(self, key, value) -> None:
        if isinstance(value, ureg.Quantity):
            super().__setitem__(key, NutritionFact(key, value))
        elif isinstance(value, NutritionFact):
            super().__setitem__(key, value)
        else:
            raise TypeError(
                f"Expected NutritionFact or Quantity, got: {type(value)}"
            )

    def update(
            self,
            other: Union[
                NutritionFact,
                Iterable[NutritionFact],
                Mapping[str, ureg.Quantity],
                'NutritionSet'
            ],
            **kwargs
    ) -> None:
        if isinstance(other, NutritionFact):
            self.__setitem__(other.name, other)
        elif isinstance(other, dict):
            # Combine kwargs with other since they're both dicts
            other.update(kwargs)
            for k, v in other.items():
                if not isinstance(k, str) or not isinstance(v, ureg.Quantity):
                    raise TypeError(
                        "Expected Mapping[str, pint.quantity.Quantity], got: "
                        f"{type(k)} -> {type(v)}"
                    )
                self.__setitem__(k, v)
        elif isinstance(other, NutritionSet):
            for k, v in other.data.items():
                self.__setitem__(k, v)
        else:
            for n in other:
                if not isinstance(n, NutritionFact):
                    raise TypeError(f"Expected NutritionFact, got: {type(n)}")
                self.__setitem__(n.name, n)
