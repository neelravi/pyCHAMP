#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import argparse
import logging
import os.path
import sys

from pychamp.parser import ccData
from pychamp.io import ccopen
from pychamp.io import write


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('outputtype',
                        choices=('xyz'),
                        help='the output format to write (json/cjson are identical)')
    parser.add_argument('compchemlogfile',
                        nargs='+',
                        help='one or more computational chemistry output files to parse and convert')

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='more verbose parsing output (only errors by default)')

    parser.add_argument('-g', '--ghost',
                        type=str,
                        default=None,
                        help='Symbol to use for ghost atoms')

    parser.add_argument('-t', '--terse',
                        action='store_true',
                        help='CJSON by default is not indented for readability, saves space (indented for readability\'s sake)')

    parser.add_argument('-u', '--future',
                        action='store_true',
                        help='use experimental features (currently optdone_as_list)')

    parser.add_argument('-i', '--index',
                        type=int,
                        default=None,
                        help='optional zero-based index for which structure to extract')

    args = parser.parse_args()

    outputtype = args.outputtype
    filenames = args.compchemlogfile
    verbose = args.verbose
    terse = args.terse
    future = args.future
    index = args.index
    ghost = args.ghost

    for filename in filenames:

        # We might want to use this option in the near future.
        ccopen_kwargs = dict()
        if future:
            ccopen_kwargs['future'] = True

        print("Attempting to parse {}".format(filename))
        log = ccopen(filename, **ccopen_kwargs)

        if not log:
            print("Cannot figure out what type of computational chemistry output file '{}' is.".format(filename))
            print("Report this to the cclib development team if you think this is an error.")
            sys.exit()

        if verbose:
            log.logger.setLevel(logging.INFO)
        else:
            log.logger.setLevel(logging.ERROR)
        data = log.parse()

        print("cclib can parse the following attributes from {}:".format(filename))
        hasattrs = ['  {}'.format(attr) for attr in ccData._attrlist if hasattr(data, attr)]
        print('\n'.join(hasattrs))

        # Write out to disk.
        outputdest = '.'.join([os.path.splitext(os.path.basename(filename))[0], outputtype])
        write_kwargs = dict()
        if future:
            write_kwargs['future'] = True
        if ghost:
            write_kwargs['ghost'] = ghost
        # For XYZ files, write the last geometry unless otherwise
        # specified.
        if not index:
            index = -1
        write_kwargs['jobfilename'] = filename

        # The argument terse presently is only applicable to
        # CJSON/JSON formats
        write(data, outputtype, outputdest, indices=index, terse=terse,
                **write_kwargs)


if __name__ == "__main__":
    main()
