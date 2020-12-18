#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
