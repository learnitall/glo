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
    nf3 = glo.NutritionFact("my metric", glo.Q_(10, None))

    # Doesn't make sense to add or remove 15 from 10 grams of sodium
    # 15 what?
    with pytest.raises(TypeError):
        nf1 + 15
    with pytest.raises(TypeError):
        nf1 - 15

    _locals = {'nf1': nf1, 'nf3': nf3}
    for op in ('+', '-', '*', '/'):
        # Doesn't make sense to do these operations with strings
        with pytest.raises(TypeError):
            eval(f'nf1 {op} "I am a string"', _locals)
        with pytest.raises(ValueError):
            # Doesn't make sense to do operations with sodium and calories
            eval(f'nf1 {op} nf3', _locals)

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


def test_nutrition_fact_name_is_read_only():
    """Test that ``NutritionFact.name`` is read-only."""

    nf = glo.NutritionFact("test name")
    with pytest.raises(AttributeError):
        nf.name = "test"


def test_create_basic_nutrition_set_instance():
    """Test can create and access attributes of ``NutritionSet``."""

    ns = glo.NutritionSet(
        glo.NutritionFact("sodium", glo.Q_(10, "grams")),
        glo.NutritionFact("fat", glo.Q_(11, "grams")),
        glo.NutritionFact("my metric", glo.Q_(100, None))
    )

    assert ns["sodium"].quantity == glo.Q_(10, "grams")
    assert ns.get("fat").quantity == glo.Q_(11, "grams")
    assert ns.get("my metric").amount == 100
    assert ns.get("not here").amount == 0


def test_can_edit_nutrition_set_instance():
    """Test can edit attributes of ``NutritionSet``."""

    ns = glo.NutritionSet()
    ns["sodium"] = glo.NutritionFact("sodium", glo.Q_(10, "grams"))
    assert ns["sodium"].quantity == glo.Q_(10, "grams")
    ns["sodium"] -= glo.Q_(5, "grams")
    assert ns["sodium"].quantity == glo.Q_(5, "grams")
    ns["sodium"] = glo.Q_(5, "milligrams")
    assert ns.get("sodium").quantity == glo.Q_(5, "milligrams")

    ns["fat"] = glo.Q_(11, "grams")
    assert ns["fat"].amount == 11
    ns["fat"] += glo.Q_(10, "grams")
    assert ns["fat"].amount == 21

    del ns["fat"]
    assert ns["fat"].amount == 0


def test_update_method_nutrition_set():
    """Test that we can update a ``NutritionSet`` using its ``update`` method."""

    ns = glo.NutritionSet()
    nf1 = glo.NutritionFact("sodium", glo.Q_(10, "grams"))
    nf2 = glo.NutritionFact("fat", glo.Q_(11, "grams"))
    nf3 = glo.NutritionFact("my metric", glo.Q_(100, None))
    ns2 = glo.NutritionSet(
        glo.NutritionFact("protein", glo.Q_(15, "grams"))
    )

    for nf_name in ("sodium", "fat", "my metric", "protein"):
        assert ns.get(nf_name).amount == 0

    ns.update(nf1)
    assert ns["sodium"].amount == 10
    ns.data = dict()

    ns.update({"fat": nf2.quantity})
    assert ns["fat"].amount == 11
    ns.data = dict()

    ns.update([nf1, nf2, nf3])
    assert ns["sodium"].amount == 10
    assert ns["fat"].amount == 11
    assert ns["my metric"].amount == 100
    ns.data = dict()

    ns.update((_ for _ in [nf1, nf2, nf3]))  # check we can use iters
    assert ns["sodium"].amount == 10
    assert ns["fat"].amount == 11
    assert ns["my metric"].amount == 100
    ns.data = dict()

    ns.update(ns2)
    assert ns["protein"].amount == 15


def test_update_method_when_given_bad_types():
    """Test ``NutritionSet.update`` raises ``TypeErrors`` appropriately."""

    bad_params = [
        '10',
        10,
        range(15),
        glo.Q_(10, "grams"),
        {'sodium': 15},
        {15: glo.Q_(10, "grams")}
    ]

    ns = glo.NutritionSet()

    for bad_param in bad_params:
        with pytest.raises(TypeError):
            ns.update(bad_param)


def test_update_method_nutrition_set_raises_errors_on_bad_types():
    """Test that ``TypeError` is raised with ``NutritionSet.update``."""

    ns = glo.NutritionSet()
    args = (
        "hey there",
        {10: glo.Q_(10, "grams")},
        {"sodium", 10},
        153
    )
    for a in args:
        with pytest.raises(TypeError):
            ns.update(a)

    with pytest.raises(TypeError):
        ns[10] = glo.Q_(10, "grams")
        test = ns[10]


def test_nutrition_fact_as_dict_method():
    """Test that ``as_dict`` method returns correct dict representation."""

    ns = glo.NutritionSet(
        glo.NutritionFact("sodium", glo.Q_(10, "grams")),
        glo.NutritionFact("fat", glo.Q_(11, "grams")),
        glo.NutritionFact("my metric", glo.Q_(100, None))
    )

    assert ns.as_dict() == {
        "sodium": glo.Q_(10, "grams"),
        "fat": glo.Q_(11, "grams"),
        "my metric": glo.Q_(100, None)
    }


def test_can_add_and_subtract_nutrition_set_instances():
    """Test that we can add and subtract ``NutritionSet`` instances."""

    ns_dict1 = {
        'sodium': glo.Q_(10, 'milligrams'),
        'fat': glo.Q_(15, 'grams'),
        'protein': glo.Q_(5, 'grams')
    }
    ns_dict2 = {
        'sodium': glo.Q_(5, 'grams'),
        'fat': glo.Q_(15, 'grams'),
        'trans fat': glo.Q_(8, 'grams')
    }

    ns1 = glo.NutritionSet()
    ns1.update(ns_dict1)

    ns2 = glo.NutritionSet()
    ns2.update(ns_dict2)

    assert (ns1 + ns2).as_dict() == {
        'sodium': glo.Q_(5010, 'milligram'),
        'fat': glo.Q_(30, 'grams'),
        'protein': glo.Q_(5, 'grams'),
        'trans fat': glo.Q_(8, 'grams')
    }

    assert (ns1 - ns2).as_dict() == {
        'sodium': glo.Q_(-4990, 'milligram'),
        'fat': glo.Q_(0, 'grams'),
        'protein': glo.Q_(5, 'grams'),
        'trans fat': glo.Q_(-8, 'grams')
    }