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
import setuptools


classifiers = """Development Status :: under development
Environment :: Console
Intended Audience :: Science/Research
Intended Audience :: users and developers of quantum chemistry codes
License :: []  License
Natural Language :: English
Operating System :: OS Independent
Programming Language :: Python (3.6 and above preffered)
Topic :: Scientific/Engineering :: Chemistry, Physics, Materials Science
Topic :: Software Development :: Libraries :: Python Modules"""


def setup_cclib():

    doclines = __doc__.split("\n")

    setuptools.setup(
        name="pyCHAMP",
        version="1.0",
        url="http://trex-coe.eu/",
        author="Ravindra Shinde and others",
        author_email="r.l.shinde@utwente.nl",
        maintainer="TREX-COE",
        maintainer_email="r.l.shinde@utwente.nl",
        license="Choose a License",
        description=doclines[0],
        long_description="\n".join(doclines[2:]),
        classifiers=classifiers.split("\n"),
        platforms=["Any."],
        packages=setuptools.find_packages(exclude=['*test*']),
        entry_points={
            'console_scripts': [
                'pyread=pychamp.scripts.read:pychampread',
                'pywrite=pychamp.scripts.write:pychampwrite',
            ]
        },
        install_requires=[
            "packaging>=19.0",
            "numpy",
            "periodictable",
        ],

    )


if __name__ == '__main__':
    pychamp()
