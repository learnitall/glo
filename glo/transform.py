#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Classes for working with Transforms compatible with pytorch."""
from typing import List
import functools
from sklearn.preprocessing import FunctionTransformer


class BaseTransform(FunctionTransformer):
    """
    Base Class of a pytorch and sklearn compatible transform.

    To use, override the ``__call__`` method. This will be passed
    to the FunctionTransformer on initialization.
    """

    def __init__(self, **kwargs):
        kwargs["func"] = self.__call__
        super().__init__(**kwargs)

    def __call__(self, sample):
        return sample


class TransformCompose(BaseTransform):
    """
    Chain more than one ``BaseTransform`` together.

    Implementation of the same class from the torch vision library.

    Parameters
    ----------
    transforms: list of BaseTransforms
        List of transforms to chain together. Sets ``transforms``
        attribute.

    Attributes
    ----------
    tranforms: list of BaseTransforms.

    Examples
    --------
    >>> from glo.transform import TransformCompose
    >>> add_five = lambda a: a + 5
    >>> mult_five = lambda a: a * 5
    >>> tc = TransformCompose([add_five, mult_five, add_five])
    >>> tc(5)
    55
    >>> add_five(mult_five(add_five(5)))
    55
    """

    def __init__(self, transforms: List[BaseTransform], **kwargs):
        super().__init__(**kwargs)
        self.transforms = transforms

    def __call__(self, sample):
        return functools.reduce(
            lambda output, t_func: t_func(output), self.transforms, sample
        )
