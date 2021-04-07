#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from glo.features._ureg import Q_, _Q_class, simplified_div


def test_Q_class_passes_is_instance_call():
    """Assert _Q_class can be used to determine Quantity instances."""

    my_quantity = Q_("10 seconds")
    assert isinstance(my_quantity, _Q_class)
    assert my_quantity.__class__ == _Q_class


def test_simplified_div_works_as_expected():
    """Test we can use simplified_div to divide quantities."""

    tests = (
        ("10 seconds", "5 seconds", 2),
        ("15 seconds ** 2", "5 seconds", None),
        ("40 ounces", "8 ounces", 5),
        ("45 ounces", "8 floz", None)
    )

    for q1, q2, result in tests:
        q1, q2 = Q_(q1), Q_(q2)
        if result is None:
            with pytest.raises(TypeError):
                simplified_div(q1, q2)
        else:
            assert simplified_div(q1, q2) == result
