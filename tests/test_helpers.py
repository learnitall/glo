#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from glo.helpers import MultiMethod, multimethod


def test_MultiMethod_type_errors():
    """Assert MultiMethod raises ``TypeError`` where appropriate."""

    mm = MultiMethod("test")

    def test(a, b):
        return a * b

    def test2(a, b):
        return a + b

    with pytest.raises(TypeError):
        mm(5, 6)

    mm.register((int, int), test)
    assert mm(5, 6) == test(5, 6)

    with pytest.raises(TypeError):
        mm.register((int, int), test2)

    with pytest.raises(TypeError):
        mm("this is", " my string")
    mm.register((str, str), test2)
    assert mm("this is", " my string") == test2("this is", " my string")

    with pytest.raises(TypeError):
        mm(5.6, 15.5)
    mm.register((float, float), test2)
    assert mm(36.5, 45.6) == test2(36.5, 45.6)
