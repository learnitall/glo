#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from typing import Set
from glo.units import BaseUnitParser
from glo.features.serving import get_num_servings


def test_get_num_servings_basic_usage():
    """Test basic usage of get_num_servings."""

    tests = [
        ["15 ounces", "5 ounces", 3],
        ["5 seconds", "2 seconds", 5.0 / 2],
        ["1.5 ounces", "9/2 ounces", 1.5 / (9 / 2.0)],
    ]

    for weight, ss, result in tests:
        assert get_num_servings(weight, ss) == result


def test_get_num_servings_unit_search():
    """Test that get_num_servings can handle searching for units."""

    tests = [
        ["5 bottles / 40 ounces", "1 bottle (8 ounces)", 40 / 8.0],
        ["4.5 seconds 6/5 floz", "48 floz", (6.0 / 5) / 48.0],
        ["8 floz", "(1 cup)", 1.0],
    ]

    for weight, ss, result in tests:
        assert get_num_servings(weight, ss) == result


def test_get_num_servings_custom_unit_parser():
    """Test we can use a custom unit parser for get_num_servings."""

    class MyParser(BaseUnitParser):
        gen = iter([{"8 ounces"}, {"2 ounces"}])

        def find_unit_strs(self, s: str) -> Set[str]:
            return next(self.gen)

    my_parser = MyParser()

    assert (
        get_num_servings("0 seconds", "0 seconds", unit_parser=my_parser) == 4
    )


def test_get_num_servings_custom_div_function():
    """Test we can use a custom div function for get_num_servings."""

    def my_div_function(*args, **kwargs):
        return 1.0

    assert get_num_servings("8 seconds", "4 seconds", div_func=my_div_function)
