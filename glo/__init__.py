#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pint

ureg = pint.UnitRegistry(system='SI')
Q_ = ureg.Quantity

# Ignore E402 from PEP8
# This imports must come after definition of ureg and Q_ above
# in order to prevent circular imports
from .nutrition import *
