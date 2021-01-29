# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, the TREX development team
#
# This file is part of TREX Project (http://trex-coe.eu) and is distributed under
# the terms of the [] License.


""" 
This code is a python interface to the CHAMP code.
It will read the necessary data from the outputs of quantum chemistry packages (stored in a given directory) and 
create the necessary input files (in old and new formats).
Many functions and classes are depicted from previously available projects.
Contact the developer :: Ravindra Shinde (r.l.shinde@utwente.nl)
"""

import sys
import numpy as np
