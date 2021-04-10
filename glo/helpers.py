#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Helper functions and classes."""
from typing import Callable, Iterable, List, Tuple, Type
import string
import functools


_registry = dict()
_printable = set(string.printable)


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


def prep_ascii_str(s_in: str) -> str:
    """
    Takes in a string and prepares it for parsing.

    In this method we convert the string to all lowercase and
    remove any characters that aren't supported by the ASCII
    character set.

    Parameters
    ----------
    s_in: str
        Input string to prep.

    Returns
    -------
    str
        Prepped version of the input ``s_in``.

    Examples
    --------
    >>> from glo.helpers import prep_ascii_str
    >>> prep_ascii_str("25 Ounces")
    '25 ounces'
    >>> prep_ascii_str("some\x05string. with\x15 funny characters")
    'somestring. with funny characters'
    >>> prep_ascii_str("    some string with whitespace   ")
    'some string with whitespace'
    """

    as_ascii = "".join(filter(lambda x: x in _printable, s_in))
    return as_ascii.strip().lower()


def remove_substrings(s_in: str, subs: Iterable[str]) -> str:
    """
    Remove list of substrings from a given input string.

    Parameters
    ----------
    s_in: str
        String to remove substrings from.
    subs: iterable of str
        List of substrings to remove from the input string. Will be
        removed in the order they are iterated over.

    Returns
    -------
    str
         Input string with all substrings found in given substring
         list removed.

    Examples
    --------
    >>> from glo.helpers import remove_substrings
    >>> remove_substrings("test1 test2 test3", ["test1", "test3"])
    'test2'
    >>> remove_substrings("TEST1 TEST2 TEST3", ["test1", "test3"])
    'TEST1 TEST2 TEST3'
    >>> remove_substrings("hey there", ["y there", "hey"])
    'he'
    """

    return functools.reduce(
        lambda string, substring: string.replace(substring, "").strip(),
        subs,
        s_in,
    )


def split_in_list(in_list: Iterable[str], split_on: str) -> List[str]:
    """
    Return flattened list of split input strings.

    Let's say that there are a bunch of strings that we want to split
    on a certain character, but want the results of the splits to be
    returned in a 1D array, rather than a 2D array:

    ```python
    >>> # instead of this:
    >>> l_in = ["test1 test2", "test3 test4"]
    >>> [s.split(" ") for s in l_in]
    [['test1', 'test2'], ['test3', 'test4']]
    >>> # we have this:
    >>> from glo.helpers import split_in_list
    >>> split_in_list(l_in, " ")
    ['test1', 'test2', 'test3', 'test4']

    ```

    Parameters
    ----------
    l_in: iterable of str
        List of input strings to split.
    split_in: str
        String holding the substring that each input string will
        be split on.

    Returns
    -------
    list of str
        Flattened list containing results from the splits

    Examples
    --------
    >>> from glo.helpers import split_in_list
    >>> split_in_list(["hey this", "is a sentence."], " ")
    ['hey', 'this', 'is', 'a', 'sentence.']
    >>> split_in_list(["and then, he said: ", "wait, what's that?"], ", ")
    ['and then', 'he said:', 'wait', "what's that?"]
    """

    return functools.reduce(
        lambda results, next_str: results
        + [sub.strip() for sub in next_str.split(split_on)],
        in_list,
        list(),
    )


def contains_substring(s_in: str, subs: Iterable[str]) -> bool:
    """
    Determine if any of the given substrings is in the given string.

    Parameters
    ----------
    s_in: str
        Input string to check for given substrings.
    subs: iterable of str
        Substrings to check for in str

    Examples
    --------
    >>> from glo.helpers import contains_substring
    >>> contains_substring("this is a test", ["hey", "there"])
    False
    >>> contains_substring("this is another test", ["test", "hey", "there"])
    True
    >>> contains_substring("this is another test", ["this", "is", "another"])
    True
    >>> contains_substring("THIS IS ANOTHER TEST", ["this", "is", "another"])
    False
    """

    return any(sub_str in s_in for sub_str in subs)
