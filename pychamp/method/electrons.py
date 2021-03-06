# -*- coding: utf-8 -*-
#
"""Calculate properties for electrons."""

import logging

import numpy

from pychamp.method.calculationmethod import Method


class Electrons(Method):
    """A container for methods pertaining to electrons."""

    def __init__(self, data, progress=None, loglevel=logging.INFO, logname="Log"):

        self.required_attrs = ('atomnos','charge','coreelectrons','homos')

        super(Electrons, self).__init__(data, progress, loglevel, logname)

    def __str__(self):
        """Returns a string representation of the object."""
        return "Electrons"

    def __repr__(self):
        """Returns a representation of the object."""
        return "Electrons"

    def alpha(self):
        """Number of alpha electrons"""
        return self.data.homos[0] + 1

    def beta(self):
        """Number of beta electrons"""
        return self.data.homos[-1] + 1

    def alpha_valence(self):
        """Number of alpha valence electrons"""
        return self.data.homos[0] + 1 - int(sum(self.data.coreelectrons)/2)

    def beta_valence(self):
        """Number of beta valence electrons"""
        return self.data.homos[-1] + 1 - int(sum(self.data.coreelectrons)/2)

    def count(self, core=False):
        """Returns the electron count in system.

        Normally returns electrons used in calculation, but will include
        core electrons in pseudopotentials if core is True.
        """
        nelectrons = sum(self.data.atomnos) - self.data.charge
        if core:
            nelectrons += sum(self.data.coreelectrons)
        return nelectrons
