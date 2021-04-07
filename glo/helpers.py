#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Helper functions and classes."""
from typing import Callable, Tuple, Type


_registry = dict()


class MultiMethod:
    """
    Representation of an overloaded method.

    Takes in the name of a function and allows for registering
    various signatures with different types. When an instance of
    this class is called, the appropriated function is called based
    on the types of the given arguments.

    From a tutorial written by Guido van Rossum.  Please see
    https://www.artima.com/weblogs/viewpost.jsp?thread=101605

    Parameters
    ----------
    name: str
        Name of the function
    """

    def __init__(self, name):
        self.name = name
        self.typemap = dict()

    def __call__(self, *args):
        types = tuple(arg.__class__ for arg in args)
        function = self.typemap.get(types)
        if function is None:
            raise TypeError("No match for overloaded function.")
        return function(*args)

    def register(self, types: Tuple[Type, ...], function: Callable) -> None:
        """
        Register a new function signature.

        Parameters
        ----------
        types: tuple of classes
            Types of the arguments for the function.
        function: callable
            To be called when arguments types match ``types``.

        Raises
        ------
        TypeError
            If the given ``types`` is already registered to a function.
        """

        if types in self.typemap:
            raise TypeError(f"Duplicate registration of function {self.name}")
        self.typemap[types] = function


def multimethod(*types: Type) -> Callable:
    """
    Function decorator for supporting method overloading.

    Based on an article written by Guido van Rossum (see
    https://www.artima.com/weblogs/viewpost.jsp?thread=101605).
    Best way to see its usage is by example.

    Examples
    --------
    >>> from glo.helpers import multimethod
    >>> @multimethod(int, int)
    ... def my_func(a, b):
    ...     return a * b
    ...

    >>> @multimethod(int, int, str)
    ... def my_func(a, b, s):
    ...    return s.format(my_func(a, b))
    ...

    >>> my_func(5, 6)
    30
    >>> my_func(5, 6, "The result is: {}")
    'The result is: 30'
    """

    def register(function):
        name = function.__name__
        multi = _registry.get(name)
        if multi is None:
            multi = _registry[name] = MultiMethod(name)
        multi.register(types, function)
        return multi

    return register
