#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Torch Lightning DataModule for KingSoopers data."""
import os
import pandas as pd
import numpy as np
from sklearn.pipeline import make_pipeline
from glo.transform import BaseTransform
from glo.units import ureg, Q_, Q_class, simplified_div
from glo.features.serving import (
    ASCIIUnitParser,
    BaseUnitParser,
    get_num_servings,
)
from glo.features.allergen import (
    ASCIIAllergenParser,
    BaseAllergyParser,
)
from glo.features.nutrition import NutritionSet
from glo.helpers import replace_multiple_substrings
from .pandas import PandasDataset


PICKUP = "PICKUP"
DELIVERY = "DELIVERY"
SHIP = "SHIP"
PRICE_METHODS = {PICKUP, DELIVERY, SHIP}
COUNT_UNITS = {
    "can",
    "bottle",
    "slice",
    "pouch",
    "pouches",
    "bar",
    "egg",
    "piece",
    "stick",
    "pod",
    "package",
    "juice_box",
    "tea_bag",
    "burrito",
    "bowl",
    "wrap",
    "taco",
    "scoop",
    "packet",
    "gummy",
    "gummies",
    "gummy_vitamin",
    "frank",
    "hot_dog",
    "link",
    "meal",
    "cupcake",
    "bun",
    "tray",
    "salad",
    "meatball",
    "gummy_bear",
    "egg_roll",
    "carton",
    "shake",
    "knot",
    "garlic_knot",
    "patty",
    "roll",
    "sandwich",
}
ureg.define(f"count = [] = ct = {' = '.join(u for u in COUNT_UNITS)}")
ureg.define("@alias microgram = mcg")
# https://www.dietarysupplementdatabase.usda.nih.gov/Conversions.php
ureg.define("International_Unit = [] = IU")
ureg.define("Retinol_Activity_Equivalent = [] = mcg_RAE")
ureg.define("milliequivalent = [] = mEq = meq")


class TransformServing(BaseTransform):
    """
    Add ``servings`` column to the dataset.

    Use the ``weight`` and ``servings`` columns to parse the number
    of servings per food item and create a new column named
    ``servings``. Delete the ``weight`` and ``servings`` column after.

    Parameters
    ----------
    parser: BaseUnitParser
        Set ``parser`` attribute. Defaults to
        ``glo.features.serving.ASCIIUnitParser()``.

    Attributes
    ----------
    parser: BaseUnitParser
        Passed to ``unit_parser`` of
        ``glo.features.serving.get_num_servings``.
    """

    def __init__(self, parser: BaseUnitParser = ASCIIUnitParser(), **kwargs):
        self.parser = parser
        super().__init__(**kwargs)

    @staticmethod
    def div_func(  # pylint: disable=invalid-name
        q1: Q_class, q2: Q_class
    ) -> float:
        """
        Return float of simplified division of quantities.

        This essentially wraps ``glo.units.simplified_div`` by
        performing some extra magic requied by the King Soopers
        dataset. For instance, sometimes the King Soopers dataset
        will incorrectly use "oz" instead of "floz", and this
        function will replace "oz" to "floz" when the other unit
        is a liquid volume.

        Parameters
        ----------
        q1: pint.Quantity instance
        q2: pint.Quantity instance

        Returns
        -------
        float

        Raises
        ------
        TypeError
            If the units of the given quantities cannot be simplified to a
            dimensionless value

        See Also
        --------
        glo.units.simplified_div
        """

        if q1.units == ureg.ounce and q2.units.is_compatible_with(
            ureg.fluid_ounce
        ):
            q1 = Q_(q1.magnitude, ureg.fluid_ounce)
        elif q2.units == ureg.ounce and q1.units.is_compatible_with(
            ureg.fluid_ounce
        ):
            q2 = Q_(q2.magnitude, ureg.fluid_ounce)

        return simplified_div(q1, q2)

    def __call__(self, food_item: pd.Series) -> pd.Series:
        result = food_item.copy(deep=True)

        # king soopers reports as fl oz, pint uses floz
        weight = food_item["weight"].replace("fl oz", "floz")
        serving_size = food_item["serving"].replace("fl oz", "floz")
        try:
            servings = get_num_servings(
                weight, serving_size, div_func=self.div_func
            )
        except ValueError:
            servings = np.nan

        del result["serving"]
        del result["weight"]
        result["servings"] = servings
        return result


class TransformAllergen(BaseTransform):
    """
    Set ``allergens`` column of dataset to parsed allergens.

    Parameters
    ----------
    parser: BaseAllergyParser
        Set ``parser`` attribute. Defaults to
        ``glo.features.allergen.ASCIIAllergenParser()``

    Attributes
    ----------
    parser: BaseAllergyParser
        Allergen parser that will be used.
    """

    def __init__(
        self,
        parser: BaseAllergyParser = ASCIIAllergenParser(),
        **kwargs,
    ):
        self.parser = parser
        super().__init__(**kwargs)

    def __call__(self, food_item: pd.Series) -> pd.Series:
        result = food_item.copy(deep=True)

        result["allergens"] = self.parser.find_allergen_strs(
            food_item["allergens"]
        )
        return result


class TransformNutrition(BaseTransform):
    """
    Set ``nutrition`` column of dataset to parsed nutrition info.

    For KingSoopers, this involves making some replacements in the
    unit strings and parsing the information into a NutritionSet.

    Attributes
    ----------
    ALIASES: mapping of str to str
        Maps substrings that could be found in the unit strings
        of the nutrition dict and their replacements.

    See Also
    --------
    glo.helpers.replace_multiple_substrings
    glo.features.nutrition.NutritionSet
    """

    ALIASES = {
        "Number of International Units": "IU",
        "International Unit": "IU",
        "Grams Per Cubic Centimetre": "g / cm ** 3",
    }

    def __call__(self, food_item: pd.Series) -> pd.Series:
        result = food_item.copy(deep=True)

        for key, value in result["nutrition"].items():
            result["nutrition"][key] = replace_multiple_substrings(
                value, self.ALIASES
            )

        result["nutrition"] = NutritionSet.from_dict(result["nutrition"])
        return result


class TransformPrice(BaseTransform):
    """
    Set ``price`` column of dataset to price of picked price method.

    King Soopers' website presents multiple methods for obtaining
    their products, with each method having a potentially different
    price. The scrapy spider will pull each of these and create a
    dictionary which maps the method to the associated price. This
    transform lets us pick which price to use.

    If the given method cannot be found for the item, then ``np.nan``
    is used instead.

    Parameters
    ----------
    method: str
        The method whose price should be set in the ``price`` column.
        Should be one of the strings in ``PRICE_METHODS``. Defaults
        to ``PICKUP``.

    Attributes
    ----------
    method: str, optional
        Set to the given method parameter.

    Raises
    ------
    ValueError
        If the given method is not in ``PRICE_METHODS``
    """

    def __init__(self, method: str = PICKUP, **kwargs):
        if method not in PRICE_METHODS:
            raise ValueError(
                f"Expected method to be one of {list(PRICE_METHODS)}, "
                f"instead got: {method}"
            )

        self.method = method
        super().__init__(**kwargs)

    def __call__(self, sample: pd.Series) -> pd.Series:
        result = sample.copy(deep=True)
        result["price"] = sample["price"].get(self.method, np.nan)
        return result


class ScrapyKingSoopersDataSet(PandasDataset):
    """
    Load and clean a raw KingSoopers Scrapy Dataset.

    The KingSoopers scrapy spider included within GLO outputs
    a single JL file which can be loaded and cleaned by this
    dataset.

    Parameters
    ----------
    file_path: str
        Location of JL file to load. Can be absolute or relative.
    is_clean: bool, optional
        If True, then will not try to clean the loaded data; assumes
        the loaded data is already clean. Defaults to False.
    price_method: str, optional
        Used in ``TransformPrice``. Please see its documentation for
        more information.

    Attributes
    ----------
    frame: pandas Dataframe
        Pandas DataFrame that contains the data.
    transforms: TransformCompose
        TransformCompose instance which represents the steps for
        cleaning the KingSoopers dataset.

    See Also
    --------
    glo.data.kingsoopers.TransformNutrition
    glo.data.kingsoopers.TransformNutrition
    glo.data.kingsoopers.TransformPrice
    glo.data.kingsoopers.TransformServing
    """

    def __init__(
        self,
        file_path: str,
        is_clean: bool = False,
        price_method: str = PICKUP,
    ):
        self.file_path = os.path.abspath(file_path)
        self.is_clean = is_clean
        """
        self.transform = TransformCompose(
            [
                TransformNutrition(),
                TransformAllergen(),
                TransformServing(),
                TransformPrice(method=price_method),
            ]
        )
        """
        self.transform = make_pipeline(
            TransformNutrition(),
            TransformAllergen(),
            TransformServing(),
            TransformPrice(method=price_method),
        )

        super().__init__(
            pd.read_json(
                self.file_path, orient="columns", typ="frame", lines=True
            ).dropna()
        )

    def __getitem__(self, idx):
        return self.transform.fit_transform(super().__getitem__(idx))
