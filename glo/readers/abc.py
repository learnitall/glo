#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Abstract Base Classes for readers."""
from abc import ABC, abstractmethod
from torch.utils.data.dataset import Dataset


class BaseReader(ABC):
    """
    Abstract Base Class for Reader classes.

    A Reader class have a ``read`` method which returns a
    ``pytorch.utils.data.Dataset`` instance.
    """

    @abstractmethod
    def read(self, *args, **kwargs) -> Dataset:
        """
        Read data from a source and return a torch Dataset.
        """
