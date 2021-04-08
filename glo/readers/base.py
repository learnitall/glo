#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Abstract Base Classes for readers."""
from abc import ABC, abstractmethod
from torch.utils.data.dataset import Dataset


class BaseReader(ABC):  # pylint: disable=too-few-public-methods
    """
    Abstract Base Class for Reader classes.

    A Reader class have a ``read`` method which returns a
    ``pytorch.utils.data.Dataset`` instance. Note that the
    torch Dataset class is abstract; a subclass must be returned
    from the read method.
    """

    @abstractmethod
    def read(self) -> Dataset:
        """
        Read data from a source and return a torch Dataset.

        Takes no parameters.

        Returns
        -------
        Subclass of abstract torch Dataset class.

        See Also
        --------
        glo.data
        """
