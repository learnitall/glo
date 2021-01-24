#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
import glo


def test_can_create_and_use_product_class():
    """Test we can create and use attributes of ``glo.Product``."""

    my_product = glo.Product('my_product', '12345678', 15.0)
    assert my_product.name == 'my_product'
    assert my_product.upc == '12345678'
    assert my_product.price == 15.0

    my_second_product = glo.Product('my_second_product')
    assert my_second_product.name == 'my_second_product'
    assert my_second_product.upc is None
    assert my_second_product.price is None


def test_as_dict_method_of_product_class():
    """Test ``glo.Product.as_dict()`` will output known attributes."""

    assert glo.Product('name').as_dict() == {
        'name': 'name',
        'upc': None,
        'price': None
    }

    assert glo.Product('name2', '000000000000', 0.0).as_dict() == {
        'name': 'name2',
        'upc': '000000000000',
        'price': 0.0
    }

    my_product_dict = {
        'name': 'my_product',
        'upc': '1337133713371337',
        'price': 13.37
    }

    assert glo.Product(**my_product_dict).as_dict() == my_product_dict
