#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Subclasses of pytorch's Dataset abstract class."""
from torch.utils.data.dataset import Dataset
import pandas as pd


class PandasDataset(Dataset):
    """
    Pandas-backed torch Dataset.

    Essentially a wrapper around a pandas DataFrame instance,
    allowing for a pandas DataFrame to be used as a torch
    Dataset.

    Parameters
    ----------
    frame: pandas DataFrame
        Pandas DataFrame to use in the background.

    Attributes
    ----------
    frame: pandas Dataframe
         Pandas DataFrame being used in the background.
    """

    def __init__(self, frame: pd.DataFrame):
        self.frame = frame

    def __len__(self):
        return len(self.frame)

    def __getitem__(self, idx):
        return self.frame.iloc[idx, :]
