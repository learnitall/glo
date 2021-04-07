#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from glo.features.serving import ASCIIUnitParser


def test_create_ascii_unit_parser():
    """Assert ASCIIUnitParser takes in no parameters."""

    ASCIIUnitParser()


def test_prep_str_ascii_unit_parser():
    """Assert prep_str properly prepares string for regex."""

    test_strs = {
        "25 ☆s": "25 s",
        "     lots of whitespace   ": "lots of whitespace",
        "I'M ALL✅ CAPS   ✅✅": "i'm all caps",
        "  GO AWAY 🦠 ": "go away"
    }

    aup = ASCIIUnitParser()
    for p, a in test_strs.items():
        assert aup.prep_str(p) == a


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
