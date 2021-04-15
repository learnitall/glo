#!/usr/bin/env python3
import pytest
from glo.features.allergen import AllergenList, ASCIIAllergenParser, DOA


def test_ascii_allergen_parser_works_as_expected():
    """Test accuracy of ASCIIAllergenParser.find_allergen_strs."""

    # based on data from king sooper products
    tests = [
        [
            "contains tree🦠 nuts and their derivatives. "
            "may contain soybean and its derivatives,tree "
            "nuts and their derivatives",
            {"tree nuts", "soybean", "tree nuts"},
            set(),
        ],
        [
            "undeclared does not contain declaration🦠 obligatory allergens",
            set(),
            {DOA},
        ],
        [
            "contains🦠 sunflower seeds and their derivatives. free from does "
            "not contain declaration obligatory allergens.",
            {"sunflower seeds"},
            {DOA},
        ],
        [
            "contains soybean and its derivatives,milk and its derivatives. "
            "may contain wheat🦠 and their derivatives,eggs and their "
            "derivatives,contains traces of tree nuts, i.e. almonds, various "
            "kinds of tree nuts,peanuts and their derivatives",
            {
                "soybean",
                "milk",
                "wheat",
                "eggs",
                "tree nuts",
                "almonds",
                "peanuts",
            },
            set(),
        ],
        [
            "free from crustaceans and their derivatives,wheat and their "
            "derivatives,eggs and their derivatives,fish and their "
            "derivatives,soybean and its derivatives,milk and its "
            "derivatives,tree nuts and their derivatives,peanuts and their "
            "derivatives.",
            set(),
            {
                "crustaceans",
                "wheat",
                "eggs",
                "fish",
                "soybean",
                "milk",
                "tree nuts",
                "peanuts",
            },
        ],
        [
            "not intentionally nor inherently included does not contain "
            "declaration obligatory allergens.🦠🦠🦠🦠",
            set(),
            {DOA},
        ],
        [
            "🦠🦠🦠🦠contains does not contain declaration obligatory allergens.",
            set(),
            {DOA},
        ],
        [
            "not intentionally nor inherently included does not contain "
            "declaration obligatory allergens.",
            set(),
            {DOA},
        ],
        [
            "contains cashew and 🦠🦠cashew products,walnut and walnut products,"
            "cocoa and its derivatives,almond and almond products,peanuts "
            "and their derivatives. may contain tree nuts and their "
            "derivatives. not intentionally nor inherently included eggs "
            "and their derivatives,soybean and its derivatives,milk and "
            "its derivatives",
            {
                "cashew and cashew products",
                "walnut and walnut products",
                "cocoa",
                "almond and almond products",
                "peanuts",
                "tree nuts",
            },
            {"eggs", "soybean", "milk"},
        ],
        ["this sentence doesn't have any keywords in it", None, None],
        ["same with this 🦠sentence. and this one.", None, None],
        [
            "undeclared does not contain declaration obligatory🦠 allergens.",
            set(),
            {DOA},
        ],
    ]

    aap = ASCIIAllergenParser()
    for sentence, pos, neg in tests:
        result = aap.find_allergen_strs(sentence)
        if pos is None:
            assert result is None
        else:
            assert result == AllergenList(pos, neg)
