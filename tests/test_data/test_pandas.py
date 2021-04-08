#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
import pandas as pd
import numpy as np
from torch.utils.data.dataset import Dataset
from glo.data.pandas import PandasDataset


def test_pandas_dataset_is_torch_dataset_subclass():
    """Assert PandasDataset is subclass of torch Dataset."""

    assert issubclass(PandasDataset, Dataset)


def test_pandas_dataset_wraps_pandas_frame():
    """Assert PandasDataset wraps DataFrame and has Dataset API."""

    frame = pd.DataFrame(
        np.arange(0, 6).reshape(2, -1),
        columns=["a", "b", "c"]
    )
    dataset = PandasDataset(frame)

    assert len(dataset) == len(frame)
    assert id(dataset.frame) == id(frame)

    for idx in range(len(dataset)):
        assert list(dataset[idx]) == list(frame.iloc[idx, :])
