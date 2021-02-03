# -*- coding: utf-8 -*-
#


"""A module for parsing and interpreting results from GAMESS package. This can be adapted to
any other quantum chemistry package with a modified parser file.
"""

__version__ = "1.0"

from pychamp import parser
from pychamp import method
from pychamp import io

ccopen  = io.ccopen
write = io.qcwrite
