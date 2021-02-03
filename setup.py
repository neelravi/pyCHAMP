# -*- coding: utf-8 -*-
#
#
"""
The python parser for reading GAMESS output file. The read data is 
formatted for the use in CHAMP code.
"""

import setuptools


# Chosen from http://www.python.org/pypi?:action=list_classifiers
classifiers = """Development Status :: Production
Programming Language :: Python
Topic :: Scientific/Engineering :: Chemistry
Topic :: Software Development :: Libraries :: Python Modules"""


def setup_pychamp():

    doclines = __doc__.split("\n")

    setuptools.setup(
        name="pyCHAMP",
        version="1.0",
        description=doclines[0],
        long_description="\n".join(doclines[2:]),
        classifiers=classifiers.split("\n"),
        packages=setuptools.find_packages(exclude=['*test*']),
        entry_points={
            'console_scripts': [
                'ccget=pychamp.scripts.ccget:ccget',
                'write=pychamp.scripts.write:main'
            ]
        },
        install_requires=[
            "packaging>=19.0",
            "numpy",
            "periodictable",
            "scipy>=1.2.0",
        ],

    )


if __name__ == '__main__':
    setup_pychamp()
