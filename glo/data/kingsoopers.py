#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Torch Lightning DataModule for KingSoopers data."""
import os
from typing import Optional, List
import pandas as pd
import pytorch_lightning as pl
from sklearn.pipeline import make_pipeline
from glo.units import (
    ureg,
    UnitWithSpaceParser,
)
from glo.transform import PandasFindMissing
from glo.features.serving import PandasParseServing
from glo.features.allergen import (
    PandasParseAllergen,
    PandasAllergenFilter,
)
from glo.features.nutrition import (
    PandasNutritionNormalizer,
    PandasParseNutrition,
    PandasNutritionFilter,
)
from glo.features.price import (
    PandasSetPriceMethod,
    PICKUP,
)
from glo.features.indicator import PandasIndicatorNormalizer
from glo.data.pandas import PandasDataset


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
    "softgels",
    "soft_gels",
    "tablet",
    "chewable_tablet",
    "lollipop",
}
ureg.define(f"count = [] = ct = {' = '.join(u for u in COUNT_UNITS)}")
ureg.define("@alias microgram = mcg")
ureg.define("@alias fluid_ounce = fl_oz")
# https://www.dietarysupplementdatabase.usda.nih.gov/Conversions.php
ureg.define("international_unit = [] = IU = number_of_international_units")
ureg.define("retinol_activity_equivalent = [] = mcg_rae = retinol_equivalent")
ureg.define("milliequivalent = [] = mEq = meq")


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
    EXPECTED_COLUMNS: dict
        Expected columns and there types. Will be passed to
        ``TransformMissing``.

    See Also
    --------
    glo.data.kingsoopers.TransformNutrition
    glo.data.kingsoopers.TransformNutrition
    glo.data.kingsoopers.TransformPrice
    glo.data.kingsoopers.TransformServing
    glo.data.kingsoopers.TransformMissing
    """

    EXPECTED_COLUMNS = {
        "nutrition": dict,
        "price": dict,
        "weight": str,
        "serving": str,
        "allergens": str,
    }

    def __init__(
        self,
        file_path: str,
        is_clean: bool = False,
        price_method: str = PICKUP,
    ):
        self.file_path = os.path.abspath(file_path)
        self.transform = make_pipeline(
            PandasFindMissing(self.EXPECTED_COLUMNS, True),
            PandasParseNutrition(UnitWithSpaceParser()),
            PandasParseAllergen(),
            PandasParseServing(UnitWithSpaceParser()),
            PandasSetPriceMethod(method=price_method),
        )

        super().__init__(
            pd.read_json(
                self.file_path, orient="columns", typ="frame", lines=True
            )
        )

        self.frame = self.frame.astype(object)
        if not is_clean:
            self.frame = self.transform.transform(self.frame)
            self.frame.dropna(axis=0, how="any", inplace=True)
            self.frame.reset_index(drop=True, inplace=True)


class ScrapyKingSoopersDataModule(pl.LightningDataModule):
    """
    Pytorch Lightning Data Module for working with Scrapy KS data.

    Parameters
    ----------
    filter_allergens: list of str, optional
        Allergens to filter out of the dataset. If None is given,
        then no filtering will occur.
    filter_nutrition: list of str, optional
        Nutrition facts to grab from the dataset. If None is
        given, then no filtering will occur.
    columns_drop: list of str, optional
        After transforming the dataset, drop the columns given. If
        None, then no columns are dropped.
    ds: ScrapyKingSoopersDataSet, optional
        If given, then will copy the given dataset and use it for
        creating the instance of the datamodule.
    ds_args: dict, optional
        Keyword arguments passed to ``ScrapyKingSoopersDataSet``.

    Attributes
    ----------
    columns_drop: list of str
        Saved argument given above.
    ds_args: dict
        Saved ``ds_args`` parameter. Can be edited until ``setup``
        method is called. Any edits after this point will have
        no effect.
    ks_ds: ScrapyKingSoopersDataSet
        Initialized ``ScrapyKingSoopersDataSet``. Will be created
        within ``setup`` method, but before then will just be set
        to ``None``.
    ks_filtered: Pandas DataFrame
        DataFrame of filtered ks_ds dataset, ready for normalization
    ks_norm: Pandas DataFrame
        DataFrame of normalized ks_ds dataset. Will share the
        same index as ks_full, but the same order as ks_norm_numpy.
    ks_norm_numpy: Numpy Array
        Numpy array of normalized ks_ds dataset, ready for training.
        Output of ``ks_norm.to_numpy()``
    filter: Pipeline
        Pipeline instance that will be used to filter ks dataset
        for normalization.
    transform: Pipeline
        Pipeline instance that will be used to normalize ks
        dataset for training.

    See Also
    --------
    glo.data.kingsoopers.ScrapyKingSoopersDataSet
    """

    def __init__(
        self,
        filter_allergens: List[str] = None,
        filter_nutrition: List[str] = None,
        columns_drop: List[str] = None,
        ds: ScrapyKingSoopersDataSet = None,
        ds_args: dict = None,
    ):
        super().__init__()

        self.colums_drop = columns_drop

        if ds is not None:
            self.ks_ds = ds
        else:
            self.ks_ds = None

        if ds_args is None:
            self.ds_args = dict()
        else:
            self.ds_args = ds_args

        self.ks_filtered = None
        self.ks_norm = None
        self.ks_norm_numpy = None

        filters = []
        if filter_allergens is not None:
            filters.append(PandasAllergenFilter(filter_allergens))
        if filter_nutrition is not None:
            filters.append(PandasNutritionFilter(filter_nutrition))
        self.filter = make_pipeline(*filters)

        self.transform = make_pipeline(
            PandasNutritionNormalizer(), PandasIndicatorNormalizer()
        )

    def setup(self, stage: Optional[str] = None):
        """Load and clean Scrapy Data and get splits."""

        if self.ks_ds is None:
            self.ks_ds = ScrapyKingSoopersDataSet(**self.ds_args)
        if self.ks_norm is None:
            self.ks_filtered = self.filter.fit_transform(self.ks_ds.frame)
            self.ks_filtered.dropna(axis=0, how="any", inplace=True)

            self.ks_norm = self.transform.fit_transform(self.ks_filtered)
            if self.colums_drop is not None:
                for col in self.colums_drop:
                    del self.ks_norm[col]

            self.ks_norm.dropna(axis=0, how="any", inplace=True)
            self.ks_norm_numpy = self.ks_norm.to_numpy()
