#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
import glo


def test_create_basic_nutrition_fact_instance():
    """Test can create and access attributes of `NutritionFact`."""

    nf = glo.NutritionFact("sodium", glo.Q_(10, "grams"))

    assert nf.name == "sodium"
    assert nf.units == glo.ureg.grams
    assert nf.amount == 10
    assert nf.quantity == glo.Q_(10, "grams")

    nf = glo.NutritionFact("na")
    assert nf.name == "na"
    assert nf.units == glo.ureg.dimensionless
    assert nf.amount == 0


def test_edit_basic_nutrition_fact_instance():
    """Test can edit attributes of `NutritionFact`."""

    nf = glo.NutritionFact("sodium", glo.Q_(10, "grams"))

    assert nf.units == glo.ureg.grams
    assert nf.amount == 10

    # Change units to milligrams by modifying quantity attribute
    nf.quantity = nf.quantity.to('milligrams')
    assert nf.units == glo.ureg.milligrams
    assert nf.amount == 10000

    # Change units back to grams by setting units attribute
    nf.units = glo.ureg.grams
    assert nf.units == glo.ureg.grams
    assert nf.amount == 10

    # Change quantity magnitude by setting amount attribute
    nf.amount += 10
    assert nf.amount == 20


def test_operator_overloads_nutrition_fact():
    """Test can add, subtract, multiply and divide with ``NutritionFact``."""

    nf1 = glo.NutritionFact("sodium", glo.Q_(10, "grams"))
    q = glo.Q_(30, "milligram")
    nf2 = glo.NutritionFact("sodium", glo.Q_(11.2, "grams"))
    nf3 = glo.NutritionFact("calories", glo.Q_(10, None))

    # Doesn't make sense to add or remove 15 from 10 grams of sodium
    # 15 what?
    with pytest.raises(TypeError):
        nf1 + 15
    with pytest.raises(TypeError):
        nf1 - 15

    # Doesn't make sense to do these operations with strings
    with pytest.raises(TypeError):
        nf1 + "I am a string"
    with pytest.raises(TypeError):
        nf1 - "I am a string"
    with pytest.raises(TypeError):
        nf1 * "I am a string"
    with pytest.raises(TypeError):
        nf1 / "I am a string"

    # Doesn't make sense to do operations with sodium and calories
    with pytest.raises(ValueError):
        nf1 + nf3
    with pytest.raises(ValueError):
        nf1 - nf3
    with pytest.raises(ValueError):
        nf1 * nf3
    with pytest.raises(ValueError):
        nf1 / nf3

    assert round((nf1 + q).amount, ndigits=2) == 10.03
    assert round((nf1 + nf2).amount, ndigits=1) == 21.2

    assert round((nf1 - q).amount, ndigits=2) == 9.97
    assert round((nf1 - nf2).amount, ndigits=1) == -1.2

    assert (nf1 * 2).amount == 20
    assert (nf1 * q).quantity == glo.Q_(0.3, "grams ** 2")
    assert (nf1 * nf2).quantity == glo.Q_(112, "grams ** 2")

    assert (nf1 / 2).amount == 5
    assert (nf1 / q).quantity == glo.Q_(10 / 30, "gram / milligram")
    assert (nf1 / nf2).quantity == glo.Q_(10 / 11.2, "dimensionless")
