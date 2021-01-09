#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
import glo


def test_can_create_and_use_item_class():
    """Test we can create and use attributes of ``glo.Item``."""

    my_item = glo.Item('my_item', '12345678', 15.0)
    assert my_item.name == 'my_item'
    assert my_item.upc == '12345678'
    assert my_item.price == 15.0

    my_second_item = glo.Item('my_second_item')
    assert my_second_item.name == 'my_second_item'
    assert my_second_item.upc is None
    assert my_second_item.price is None


def test_as_dict_method_of_item_class():
    """Test ``glo.Item.as_dict()`` will output known attributes."""

    assert glo.Item('name').as_dict() == {
        'name': 'name',
        'upc': None,
        'price': None
    }

    assert glo.Item('name2', '000000000000', 0.0).as_dict() == {
        'name': 'name2',
        'upc': '000000000000',
        'price': 0.0
    }

    my_item_dict = {
        'name': 'my_item',
        'upc': '1337133713371337',
        'price': 13.37
    }

    assert glo.Item(**my_item_dict).as_dict() == my_item_dict
