#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from glo.units import (
    ureg,
    Q_,
    Q_class,
    simplified_div,
    ASCIIUnitParser,
    UnitWithSpaceParser,
    get_quantity_from_str,
)


def test_Q_class_passes_is_instance_call():
    """Assert Q_class can be used to determine Quantity instances."""

    my_quantity = Q_("10 seconds")
    assert isinstance(my_quantity, Q_class)
    assert my_quantity.__class__ == Q_class


def test_simplified_div_works_as_expected():
    """Test we can use simplified_div to divide quantities."""

    tests = (
        ("10 seconds", "5 seconds", 2),
        ("15 seconds ** 2", "5 seconds", None),
        ("40 ounces", "8 ounces", 5),
        ("45 ounces", "8 floz", None),
    )

    for q1, q2, result in tests:
        q1, q2 = Q_(q1), Q_(q2)
        if result is None:
            with pytest.raises(TypeError):
                simplified_div(q1, q2)
        else:
            assert simplified_div(q1, q2) == result


def test_create_ascii_unit_parser():
    """Assert ASCIIUnitParser takes in no parameters."""

    ASCIIUnitParser()


def test_create_unit_with_space_unit_parser():
    """Assert UnitWithSpaceParser takes in no parameters."""

    UnitWithSpaceParser()


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
        "  GO AWAY 🦠 1.2 ✅cans / ✅1.2 fl oz": {"1.2 cans", "1.2 fl oz"},
    }

    aup = ASCIIUnitParser()
    for p, a in test_strs.items():
        assert aup.find_unit_strs(p) == a


def test_find_unit_strs_with_space_unit_parser():
    """Assert find_unit_strs properly finds unit strings."""

    test_strs = {
        "1.25cup (40 g)": {"1.25cup", "40 g"},
        "0.667cup cereal (30 g)": {
            "0.667cup cereal",
            "0.667cup_cereal",
            "30 g",
        },
        "34biscuits (61 g)": {"34biscuits", "61 g"},
        "3/4biscuits (6/1 g)": {"3/4biscuits", "6/1 g"},
        "12 cans / 12 fl oz": {"12 cans", "12 fl oz", "12 fl_oz"},
        "1/2 cans / 1/2 fl oz": {"1/2 cans", "1/2 fl oz", "1/2 fl_oz"},
        "1.2 cans / 1.2 fl oz": {"1.2 cans", "1.2 fl oz", "1.2 fl_oz"},
        "  GO AWAY 🦠 ": set(),
        "  GO AWAY 🦠 1.2 ✅cans / ✅1.2 fl oz": {
            "1.2 cans",
            "1.2 fl oz",
            "1.2 fl_oz",
        },
    }

    aup = UnitWithSpaceParser()
    for p, a in test_strs.items():
        assert aup.find_unit_strs(p) == a


def test_get_quantity_from_str_works_as_expected():
    """Assert basic usage of get_quantity_from_str works"""

    # make sure these are defined
    ureg.define("count = [] = ct = biscuits = can = cup_cereal")

    test_strs = {
        "1.25cup (40 g)": {"1.25cup", "40 g"},
        "0.667cup cereal (30 g)": {"30 g", "0.667 ct"},
        "34biscuits (61 g)": {"61 g", "34 ct"},
        "3/4biscuits (6/1 g)": {"6/1 g", "3/4 ct"},
        "12 cans / 12 floz": {"12 floz", "12 ct"},
        "1/2 cans / 1/2 floz": {"1/2 floz", "1/2 ct"},
        "1.2 cans / 1.2 floz": {"1.2 floz", "1.2 ct"},
        "  GO AWAY 🦠 ": set(),
        "  GO AWAY 🦠 1.2 ✅cans / ✅1.2 floz": {"1.2 floz", "1.2 ct"},
    }

    aup = UnitWithSpaceParser()
    for p, a in test_strs.items():
        assert get_quantity_from_str(p, aup) == set(map(Q_, a))
