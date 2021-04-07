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
_NSCompatibleTypes = Union[
    "NutritionFact",
    Iterable["NutritionFact"],
    Mapping[str, ureg.Quantity],
    "NutritionSet",
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
            quantity_param = other
        elif isinstance(other, NutritionFact):
            if other.name != self.name:
                raise ValueError(
                    "Refusing to operator on two NutritionFacts with "
                    f"mismatch names: {self.name} != {other.name}"
                )
            quantity_param = other.quantity
        elif isinstance(other, (float, int)):
            quantity_param = Q_(other, "dimensionless")
        else:
            raise TypeError(
                f"Invalid type for operation with NutritionFact: {type(other)}"
            )

        return operator_func(self, quantity_param)

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
        if float(quantity.m) == 0.0:
            result_quantity = self.quantity
        elif float(self.amount) == 0.0:
            result_quantity = quantity
        else:
            result_quantity = self.quantity + quantity

        return NutritionFact(self.name, result_quantity)

    @_operator_overload_wrap
    def __sub__(self, quantity):
        if float(quantity.m) == 0.0:
            result_quantity = self.quantity
        elif float(self.amount) == 0.0:
            result_quantity = -quantity
        else:
            result_quantity = self.quantity - quantity

        return NutritionFact(self.name, result_quantity)

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
    as_dict:
        Return dictionary representation of NutritionSet instance.
        See method docstring below.
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
    >>> calories = glo.NutritionFact("calories", glo.Q_(100, "calories"))
    >>> my_set.update(calories)
    >>> my_set["calories"].amount
    100
    >>> my_set += glo.NutritionSet(calories * 2)
    >>> my_set["calories"].amount
    300
    """

    def __init__(self, *facts: NutritionFact):
        """NutritionSet constructor."""

        super().__init__(facts)

    @staticmethod
    def _is_valid_key(key: str) -> None:
        """
        Check if given key is valid.

        Raises
        ------
        TypeError:
            If given key is not a string
        """

        if not isinstance(key, str):
            raise TypeError(f"Expected type str, instead got {type(key)}")

    def __getitem__(self, key) -> NutritionFact:
        self._is_valid_key(key)
        try:
            return super().__getitem__(key)
        except KeyError:
            return NutritionFact(key, None)

    def __setitem__(self, key, value) -> None:
        self._is_valid_key(key)
        if isinstance(value, ureg.Quantity):
            super().__setitem__(key, NutritionFact(key, value))
        elif isinstance(value, NutritionFact):
            super().__setitem__(key, value)
        else:
            raise TypeError(
                f"Expected NutritionFact or Quantity, got: {type(value)}"
            )

    def __sub__(self, other: _NSCompatibleTypes) -> "NutritionSet":
        """Subtract two NutritionSets together and return the result."""

        ret_ns = NutritionSet()
        ret_ns.update(self)
        ret_ns.update(other, merge_func=lambda a, b: a - b)
        return ret_ns

    def __add__(self, other: _NSCompatibleTypes) -> "NutritionSet":
        """Add two NutritionSets together and return the result."""

        ret_ns = NutritionSet()
        ret_ns.update(self)
        ret_ns.update(other, merge_func=lambda a, b: a + b)
        return ret_ns

    def as_dict(self) -> Mapping[str, Quantity]:
        """
        Return ``dict`` representing this ``NutritionSet``.

        Keys in returned dictionary are ``NutritionFact`` names, and
        values are their associated ``Quantities`` in this
        ``NutritionSet``.
        """

        return {nf.name: nf.quantity for nf in self.data.values()}

    def update(  # pylint: disable=arguments-differ
        self,
        other: _NSCompatibleTypes,
        merge_func: Union[
            None, Callable[[ureg.Quantity, ureg.Quantity], ureg.Quantity]
        ] = None,
    ) -> None:
        """
        Update the ``NutritionSet`` based on given arguments.

        Overloaded form of ``dict.update``.

        Parameters
        ----------
        other:
            Lots of options here. Can be a ``NutritionFact``, an
            iterable of ``NutritionFact`` instances, a mapping of
            strings to ``pint.quantity.Quantity``, or another
            ``NutritionSet``.
        merge_func: callable
            Callable that takes in two ``NutritionFact`` instances
            returns a single ``NutritionFact`` instance. If a key
            in ``other`` matches a key in this ``NutritionSet``,
            then the quantities from each will be passed through
            ``merge_func`` before being added into the new
            ``NutritionSet``. These two statements are equivalent:

            .. code-block: python
                NutritionFact().update(
                    NutritionFact(),
                    merge_func=lambda a, b: a + b
                )
                NutritionFact() + NutritionFact()

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
        >>> my_ns.update(
        ...     {'sodium': glo.Q_(10, 'grams')},
        ...     merge_func=lambda a, b: (a + b) * 2
        ... )
        >>> my_ns["sodium"].amount
        40
        """
        if isinstance(other, NutritionFact):
            if merge_func is not None:
                self[other.name] = merge_func(self[other.name], other)
            else:
                self.__setitem__(other.name, other)
        elif isinstance(other, dict):
            for name, quantity in other.items():
                if not isinstance(quantity, Quantity):
                    raise TypeError(
                        "Expected mapping of str -> Quantity, instead got: "
                        f"{type(name)} -> {type(quantity)}"
                    )
                self.update(
                    NutritionFact(name, quantity), merge_func=merge_func
                )
        elif isinstance(other, NutritionSet):
            for name, nut_fact in other.data.items():
                self.update(nut_fact, merge_func=merge_func)
        else:  # try assuming iterable
            try:
                for nut_fact in other:
                    if not isinstance(nut_fact, NutritionFact):
                        raise TypeError(
                            "Expected iterable to be of NutritionFact "
                            f"instances, instead got {type(nut_fact)}"
                        )
                    self.update(nut_fact, merge_func=merge_func)
            except TypeError as exception:
                if "not iterable" in exception.args[0]:
                    raise TypeError(
                        "Expected one of NutritionFact, "
                        "Mapping[str, Quantity] or NutritionSet, "
                        f"instead got: {type(other)}"
                    ) from exception

                raise exception