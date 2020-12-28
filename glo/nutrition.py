#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tools for working with and representing nutrition information."""
from typing import Any, Callable, Iterable, Mapping, Union
import collections
from pint.quantity import Quantity
from pint.unit import Unit
from ._ureg import Q_, ureg


_NFOperator = Callable[
    ["NutritionFact", Union["NutritionFact", ureg.Quantity, int, float]],
    "NutritionFact",
]


def _operator_overload_wrap(operator_func: _NFOperator) -> _NFOperator:
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
        (mainly add or sub), returning new ``NutritionFact``
        with resulting quantity.

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
        Read only name for this nutrition fact. See above parameter
        description for more information.
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

    __slots__ = ["_name", "quantity"]

    def __init__(self, name: str, quantity: Quantity = None):
        """NutritionFact constructor."""

        self._name = name

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
    def name(self):
        """Name of given nutrition fact this instance represents."""
        return self._name

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


class NutritionSet(collections.UserDict):  # pylint: disable=too-many-ancestors
    """
    Dictionary representation of a group of ``NutritionFact``.

    This class inherits from ``collections.UserDict`` and is tailored
    to make working with ``NutritionFact`` much easier. Keys in this
    specialized dictionary are the string names of ``NutritionFact``
    and values are the ``NutritionFact`` themselves.

    Parameters
    ----------
    facts: iterable
        Iterable of ``NutritionFact`` that will act as the initial
        data for the set.

    Methods
    -------
    clear:
        See ``dict.clear``.
    get:
        See ``dict.get``.
    items:
        See ``dict.items``.
    keys:
        See ``dict.keys``.
    pop:
        See ``dict.pop``.
    popitem:
        See ``dict.popitem``.
    setdefault:
        See ``dict.setdefault``.
    update:
        Overloaded from ``dict.update`` to ease working with
        ``NutritionFacts``. See method docstring below.
    values:
        See ``dict.values``.

    Examples
    --------
    >>> import glo
    >>> sodium = glo.NutritionFact("sodium", glo.Q_(10, "grams"))
    >>> protein = glo.NutritionFact("protein", glo.Q_(15, "grams"))
    >>> fat = glo.NutritionFact("fat", glo.Q_(5, "grams"))
    >>> my_set = glo.NutritionSet(sodium, protein, fat)
    >>> my_set["sodium"].amount
    10
    >>> my_set["sodium"] += glo.Q_(5, "grams")
    >>> my_set["sodium"].amount
    15
    >>> my_set["calories"].amount
    0
    >>> calories = glo.NutritionFact("calories", glo.Q_(100, None))
    >>> my_set.update(calories)
    >>> my_set["calories"].amount
    100
    """

    def __init__(self, *facts: NutritionFact):
        """NutritionSet constructor."""

        super().__init__(facts)

    def __getitem__(self, key) -> NutritionFact:
        # TODO raise TypeError if key is not str
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

    def update(  # pylint: disable=arguments-differ
        self,
        other: Union[
            NutritionFact,
            Iterable[NutritionFact],
            Mapping[str, ureg.Quantity],
            "NutritionSet",
        ],
        **kwargs,
    ) -> None:
        """
        Update the ``NutritionSet`` based on given arguments.

        Overloaded form of ``dict.update``.

        Parameters
        ----------
        other:
            Lots of options here. Can be a ``NutritionFact``, a
            iterable of ``NutritionFact``s, a mapping of strings
            to ``pint.quantity.Quantity``s or another ``NutritionSet``.

        Examples
        --------
        >>> # Say we have the following variables to start with:
        >>> import glo
        >>> sodium = glo.NutritionFact("sodium", glo.Q_(10, "grams"))
        >>> protein = glo.NutritionFact("protein", glo.Q_(15, "grams"))
        >>> fat = glo.NutritionFact("fat", glo.Q_(5, "grams"))
        >>> my_ns = glo.NutritionSet()
        >>> # We can update my_ns like so
        >>> my_ns.update(protein)
        >>> my_ns["protein"].amount
        15
        >>> my_ns.update([sodium, fat])
        >>> my_ns.get("sodium").amount
        10
        >>> my_ns.get("fat").amount
        5
        >>> # Clear my_ns
        >>> my_ns.data = dict()
        >>> my_ns.update(
        ...    {nf.name: nf.quantity for nf in [sodium, protein, fat]}
        ... )
        >>> print(
        ...     f"{my_ns['sodium'].amount}, "
        ...     f"{my_ns['protein'].amount}, "
        ...     f"{my_ns['fat'].amount}"
        ... )
        10, 15, 5
        """
        if isinstance(other, NutritionFact):
            self.__setitem__(other.name, other)
        elif isinstance(other, dict):
            # Combine kwargs with other since they're both dicts
            other.update(kwargs)
            for key, val in other.items():
                if not isinstance(key, str) or not isinstance(
                    val, ureg.Quantity
                ):
                    raise TypeError(
                        "Expected Mapping[str, pint.quantity.Quantity], got: "
                        f"{type(key)} -> {type(val)}"
                    )
                self.__setitem__(key, val)
        elif isinstance(other, NutritionSet):
            for key, val in other.data.items():
                self.__setitem__(key, val)
        else:
            for nut_fact in other:
                if not isinstance(nut_fact, NutritionFact):
                    raise TypeError(
                        f"Expected NutritionFact, got: {type(nut_fact)}"
                    )
                self.__setitem__(nut_fact.name, nut_fact)
