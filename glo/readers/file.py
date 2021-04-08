#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Readers that load data from disk."""
import os
from typing import Iterator
from .abc import BaseReader
import json
import pandas as pd
from glo.data.pandas import PandasDataset


class FileReader(BaseReader):
    """
    Basic class for reading data from a file.

    Meant to be subclassed, this class is built to handle the
    tedious aspects of reading from files, such as relative paths,
    going through lines, etc. Make sure to override the

    Parameters
    ----------
    file_path: str
         File path of the file to read. Can be absolute or relative.
    mode: str
         Mode to open the file with. Defaults to "rb".

    Attributes
    ----------
    file_path: str
         Absolute path of given ``file_path``.
    mode: str
         Mode that the file will be opened with.
    """

    def __init__(self, file_path: str, mode: str = "rb"):
        self.file_path = os.path.abspath(file_path)
        self.mode = mode

    def lines(self) -> Iterator[str]:
        """
        Return a generator that yields each line in the file.

        Parameters
        ----------
        mode: str
             Mode to open the file as

        Returns
        -------
        generator of str

        Raises
        ------
        OSError
             if unable to open file from ``self.file_path``
        """

        with open(self.file_path, self.mode) as file_obj:
            line = file_obj.readline()
            while len(line) > 0:
                yield line.strip()
                line = file_obj.readline()


class ScrapyJLReader(FileReader):
    """
    Read data from a JL (JSON-Line) file created by Scrapy.

    A JL file is a JSON file, where each line is independent.
    It's used in Scrapy commonly for exporting items from a spider
    (see https://docs.scrapy.org/en/latest/intro/overview.html).
    For this Reader, it's assumed that each line is a dict, with
    keys as columns and each line containing a row of data.
    Reads the data from the JL file and returns a PandasDataset
    from glo.data.

    Parameters
    ----------
    file_path: str
         File path of the JL file to read. Can be absolute or
         relative.
    mode: str
         Mode to open the JL file with. Defaults to "rb".

    Attributes
    ----------
    file_path: str
         Absolute path of given ``file_path``.
    mode: str
         Mode that the JL file will be opened with.
    """

    def read(self) -> PandasDataset:
        """
        Read the JL file from disk and return a PandasDataset

        Raises
        ------
        OSError
             If unable to read JL file.
        ValueError
             If unable to parse JSON data from the file.

        See Also
        --------
        glo.data.pandas.PandasDataset
        """

        frame = pd.DataFrame([json.loads(line) for line in self.lines()])
        return PandasDataset(frame)
