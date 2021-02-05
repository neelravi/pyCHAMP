# -*- coding: utf-8 -*-
#
"""Contains all writers for standard chemical representations."""


from pychamp.io.xyzreader import XYZ as XYZReader
from pychamp.io.xyzwriter import XYZ as XYZWriter

from pychamp.io.ccio import ccopen
from pychamp.io.ccio import qcread
from pychamp.io.ccio import qcwrite
from pychamp.io.ccio import write_champ_old_sym
from pychamp.io.ccio import write_champ_old_geo
from pychamp.io.ccio import write_champ_old_lcao

from pychamp.io.ccio import URL_PATTERN
