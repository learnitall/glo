#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tools for working with and representing allergy information."""
from typing import NamedTuple, Set, Union
from abc import ABC, abstractmethod
from glo.helpers import (
    contains_substring,
    prep_ascii_str,
    remove_substrings,
    split_in_list,
)


DOA = "declaration obligatory allergens"


class AllergenList(NamedTuple):
    """
    NamedTuple to represent a list of Allergens.

    Attributes
    ----------
    contains: set of str
        Set of allergens that are contained in food item.
    free_from: set of str
        Set of allergens that are explicitly not contained
        in a food item.
    """

    contains: Set[str]
    free_from: Set[str]


class BaseAllergyParser(ABC):
    """
    ABC of an AllergyParser class.

    An AllergyParser class implements the ``find_allergen_strs``
    method, which takes in a string and returns an AllergenList
    instance.
    """

    @abstractmethod
    def find_allergen_strs(self, s_in: str) -> AllergenList:
        """
        Get set of possible unit substrings from input string.

        Parameters
        ----------
        s_in: str
            Input string to search through

        Returns
        -------
        set of str
            Set of possible unit substrings in input ``s_in``.
        """


class ASCIIAllergenParser(BaseAllergyParser):
    """
    Parses allergens from ASCII strings.

    Assumes that each sentence in the given input text will either
    declare that the item has an allergy or that the item is free from
    an allergy. Each sentence is assumed to start with one of the
    following substrings, which states whether or not the sentence
    will be positive (contains) or negative (free from):

    * Positive
        * ``contains``
        * ``derived from``
        * ``may contain``
    * Negative
        * ``free from``
        * ``not intentionally nor inherently included``
        * ``does not contain``

    After a positive or negative keyword in a sentence, it is
    assumed that what follows is a comma separated list of allergens.

    If a sentence contains both a positive and a negative keyword,
    then the last keyword is trusted.

    Here's some example allergen text strings that are supported:

    * "Contains wheat, bread, chocolate. Free from peanuts."
    * "Does not contain chicken. Contains beef."

    Attributes
    ----------
    POSITIVE: set of str
        Set of keywords that denote an allergy is contained.
    NEGATIVE: set of str
        Set of keywords that denote an allergy is not contained.
    KEYWORDS: set of str
        Union of POSITIVE and NEGATIVE
    TO_REMOVE: set of str
        A list of common substrings to remove from the input string
        before parsing.
    """

    POSITIVE = {"contains", "derived from", "may contain"}
    NEGATIVE = {
        "free from",
        "not intentionally nor inherently included",
        "does not contain",
        "undeclared",
    }
    KEYWORDS = POSITIVE.union(NEGATIVE)
    TO_REMOVE = {
        "and their derivatives",
        "and its derivatives",
        "i.e.",
        "traces of",
        "various kinds of",
    }

    def find_allergen_strs(self, s_in: str) -> Union[AllergenList, None]:
        """
        Get set of possible allergen substrings from input string.

        It may be assumed from the user that the allergens within
        the ``AllergenList`` will be unique ASCII strings in all
        lowercase.

        Parameters
        ----------
        s_in: str
            Input string to search through

        Returns
        -------
        set of str
            Set of possible allergen substrings in input ``s_in``.
        None
            If no posseble allergin substrings were found.

        Examples
        --------
        >>> from glo.features.allergen import ASCIIAllergenParser
        >>> aap = ASCIIAllergenParser()
        >>> res = aap.find_allergen_strs("Contains nuts, treenuts, peanuts.")
        >>> f"Contains: {', '.join(sorted(list(res.contains)))}"
        'Contains: nuts, peanuts, treenuts'
        >>> res = aap.find_allergen_strs("Free from WHEAT, GLUTEN.")
        >>> f"Free from: {', '.join(sorted(list(res.free_from)))}"
        'Free from: gluten, wheat'
        >>> aap.find_allergen_strs("May contain free from any allergens")
        AllergenList(contains=set(), free_from={'any allergens'})
        >>> aap.find_allergen_strs("There are no allergens in here.") is None
        True
        >>> aap.find_allergen_strs("May contain traces of peanuts.")
        AllergenList(contains={'peanuts'}, free_from=set())
        """

        sentences = remove_substrings(
            prep_ascii_str(s_in), self.TO_REMOVE
        ).split(".")
        pos = list()
        neg = list()
        for sentence in sentences:
            sentence = sentence.strip()
            # don't do anything on empty lines or if the sentence doesn't
            # have any keywords we can recognize.
            if sentence == "" or not contains_substring(
                sentence, self.KEYWORDS
            ):
                break

            # sentence with positive keywords only
            sentence_pos = remove_substrings(sentence, self.NEGATIVE)
            # sentence with negative keywords only
            sentence_neg = remove_substrings(sentence, self.POSITIVE)

            # if we remove all negative keywords and the sentence remains
            # the same, then assume it may be positive
            if sentence_pos == sentence:
                # Since the sentence has positive keywords, and we
                # want just the allergens, add the sentence with all
                # positive keywords removed
                pos.append(sentence_neg)
            elif sentence_neg == sentence:
                neg.append(sentence_pos)
            else:
                # in this case we have a mix of positive and negative
                # keywords and we need to assume that the last keyword
                # should be trusted
                sentence_no_keywords = remove_substrings(
                    sentence, self.KEYWORDS
                )

                # if the sentence with all negative keywords removed is a
                # valid substring, then we can assume that the negative
                # keyword comes before:
                # "does not contain may contain peanuts"
                # pos: "may contain peanuts" (substring index is 16)
                # neg: "does not contain peanuts" (substring not found)
                if sentence_pos in sentence:
                    pos.append(sentence_no_keywords)
                else:
                    neg.append(sentence_no_keywords)

        allergen_list = AllergenList(
            contains=set(split_in_list(pos, ",")),
            free_from=set(split_in_list(neg, ",")),
        )

        if allergen_list.contains.union(allergen_list.free_from) == set():
            return None

        return allergen_list
