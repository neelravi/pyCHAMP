# -*- coding: utf-8 -*-
#

"""Abstract based class for cclib methods."""

import logging
import sys

class MissingAttributeError(Exception):
    pass

class Method:
    """Abstract base class for all cclib method classes.

    All the modules containing methods should be importable.
    """
    required_attrs = ()
    def __init__(self, data, progress=None, loglevel=logging.INFO, logname="Log"):
        """Initialise the Logfile object.

        This constructor is typically called by the constructor of a subclass.
        """

        self.data = data
        self.progress = progress
        self.loglevel = loglevel
        self.logname = logname
        self._check_required_attributes()
        self.logger = logging.getLogger('%s %s' % (self.logname, self.data))
        self.logger.setLevel(self.loglevel)
        self.logformat = "[%(name)s %(levelname)s] %(message)s"
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(self.logformat))
        self.logger.addHandler(handler)

    def _check_required_attributes(self):
        """Check if required attributes are present in data."""
        missing = [x for x in self.required_attrs
                    if not hasattr(self.data, x)]
        if missing:
            missing = ' '.join(missing)
            raise MissingAttributeError(
                'Could not parse required attributes to use method: ' + missing)
