#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from typing import Set
from glo.features.serving import BaseUnitParser, \
    ASCIIUnitParser, get_num_servings


def test_create_ascii_unit_parser():
    """Assert ASCIIUnitParser takes in no parameters."""

    ASCIIUnitParser()


def test_find_unit_strs_ascii_unit_parser():
    """Assert find_unit_strs properly finds unit strings."""

    test_strs = {
        "1.25cup (40 g)": {"1.25cup", "40 g"},
        "0.667cup cereal (30 g)": {"0.667cup cereal", "30 g"},
        "34biscuits (61 g)": {"34biscuits", "61 g"},
        "3/4biscuits (6/1 g)": {"3/4biscuits", "6/1 g"},
        "12 cans / 12 fl oz": {"12 cans", "12 fl oz"},
        "1/2 cans / 1/2 fl oz": {"1/2 cans", "1/2 fl oz"},
        "1.2 cans / 1.2 fl oz": {"1.2 cans", "1.2 fl oz"},
        "  GO AWAY 🦠 ": set(),
        "  GO AWAY 🦠 1.2 ✅cans / ✅1.2 fl oz": {"1.2 cans", "1.2 fl oz"}
    }

    aup = ASCIIUnitParser()
    for p, a in test_strs.items():
        assert aup.find_unit_strs(p) == a


def test_get_num_servings_basic_usage():
    """Test basic usage of get_num_servings."""

    tests = [
        ["15 ounces", "5 ounces", 3],
        ["5 seconds", "2 seconds", 5.0 / 2],
        ["1.5 ounces", "9/2 ounces", 1.5 / (9/2.0)]
    ]

    for weight, ss, result in tests:
        assert get_num_servings(weight, ss) == result


def test_get_num_servings_unit_search():
    """Test that get_num_servings can handle searching for units."""

    tests = [
        ["10 bottles / 45 ounces", "1 bottle (8 ounces)", 45 / 8.0],
        ["4.5 seconds 6/5 floz", "48 floz", (6.0 / 5) / 48.0],
        ["8 floz", "(1 cup)", 1.0]
    ]

    for weight, ss, result in tests:
        assert get_num_servings(weight, ss) == result


def test_get_num_servings_custom_unit_parser():
    """Test we can use a custom unit parser for get_num_servings."""

    class MyParser(BaseUnitParser):
        gen = iter([
            {"8 ounces"},
            {"2 ounces"}
        ])

        def find_unit_strs(self, s: str) -> Set[str]:
             return next(self.gen)

    my_parser = MyParser()

    assert get_num_servings(
        "0 seconds", "0 seconds", unit_parser=my_parser) == 4

def test_get_num_servings_custom_div_function():
    """Test we can use a custom div function for get_num_servings."""

    def my_div_function(*args, **kwargs):
        return 1.0

    assert get_num_servings(
         "8 seconds", "4 seconds", div_func=my_div_function
    )
