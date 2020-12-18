#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Initialize unit registry from ``pint`` module."""
import pint

ureg = pint.UnitRegistry(system='SI')
Q_ = ureg.Quantity
