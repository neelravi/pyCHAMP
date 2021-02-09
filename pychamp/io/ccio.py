# -*- coding: utf-8 -*-
#
"""Tools for identifying, reading and writing files."""

import atexit
import io
import os
import sys
import re
import numpy as np
from tempfile import NamedTemporaryFile
from urllib.request import urlopen
from urllib.error import URLError

from pychamp.parser import data
from pychamp.parser import logfileparser
from pychamp.parser.utils import find_package

from pychamp.parser.gamessparser import GAMESS

from pychamp.io import xyzreader
from pychamp.io import xyzwriter

#  Core is needed to compute the core number of electrons
from pychamp.parser.utils import Core
#  periodic table is essential here
import periodictable as pt

np.set_printoptions(threshold=sys.maxsize)



_has_cclib2openbabel = find_package("openbabel")
if _has_cclib2openbabel:
    from pychamp.bridge import cclib2openbabel


# Regular expression for validating URLs
URL_PATTERN = re.compile(

    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE

)

# Parser choice is triggered by certain phrases occurring the logfile. Where these
# strings are unique, we can set the parser and break. In other cases, the situation
# is a little but more complicated. Here are the exceptions:
#   1. The GAMESS trigger also works for GAMESS-UK files, so we can't break
#      after finding GAMESS in case the more specific phrase is found.
#   2. Molpro log files don't have the program header, but always contain
#      the generic string 1PROGRAM, so don't break here either to be cautious.
#   3. "MOPAC" is used in some packages like GAMESS, so match MOPAC20##
#
# The triggers are defined by the tuples in the list below like so:
#   (parser, phrases, flag whether we should break)
triggers = [ (GAMESS, ["GAMESS"], False)  ]

readerclasses = {
    'xyz': xyzreader.XYZ,
}

writerclasses = {
    'xyz': xyzwriter.XYZ,
}


class UnknownOutputFormatError(Exception):
    """Raised when an unknown output format is encountered."""


def guess_filetype(inputfile):
    """Try to guess the filetype by searching for trigger strings."""
    if not inputfile:
        return None

    filetype = None
    if isinstance(inputfile, str):
        for line in inputfile:
            for parser, phrases, do_break in triggers:
                if all([line.lower().find(p.lower()) >= 0 for p in phrases]):
                    filetype = parser
                    if do_break:
                        return filetype
    else:
        for fname in inputfile:
            for line in inputfile:
                for parser, phrases, do_break in triggers:
                    if all([line.lower().find(p.lower()) >= 0 for p in phrases]):
                        filetype = parser
                        if do_break:
                            return filetype
    return filetype


def qcread(source, *args, **kwargs):
    """Attempt to open and read computational chemistry data from a file.

    If the file is not appropriate for cclib parsers, a fallback mechanism
    will try to recognize some common chemistry formats and read those using
    the appropriate bridge such as Open Babel.

    Inputs:
        source - a single logfile, a list of logfiles (for a single job),
                 an input stream, or an URL pointing to a log file.
        *args, **kwargs - arguments and keyword arguments passed to ccopen
    Returns:
        a ccData object containing cclib data attributes
    """

    log = ccopen(source, *args, **kwargs)
    if log:
        if kwargs.get('verbose', None):
            print('Identified logfile to be in %s format' % log.logname)
        # If the input file is a CJSON file and not a standard compchemlog file
        cjson_as_input = kwargs.get("cjson", False)
        if cjson_as_input:
            return log.read_cjson()
        else:
            return log.parse()
    else:
        if kwargs.get('verbose', None):
            print('Attempting to use fallback mechanism to read file')
        return fallback(source)


def ccopen(source, *args, **kwargs):
    """Guess the identity of a particular log file and return an instance of it.

    Inputs:
        source - a single logfile, a list of logfiles (for a single job),
                 an input stream, or an URL pointing to a log file.
        *args, **kwargs - arguments and keyword arguments passed to filetype

    Returns:
        GAMESS object
    """
    inputfile = None
    is_stream = False

    # Check if source is a link or contains links. Retrieve their content.
    # Try to open the logfile(s), using openlogfile, if the source is a string (filename)
    # or list of filenames. If it can be read, assume it is an open file object/stream.
    is_string = isinstance(source, str)
    is_url = True if is_string and URL_PATTERN.match(source) else False
    is_listofstrings = isinstance(source, list) and all([isinstance(s, str) for s in source])
    if is_string or is_listofstrings:
        # Process links from list (download contents into temporary location)
        if is_listofstrings:
            filelist = []
            for filename in source:
                if not URL_PATTERN.match(filename):
                    filelist.append(filename)
                else:
                    try:
                        response = urlopen(filename)
                        tfile = NamedTemporaryFile(delete=False)
                        tfile.write(response.read())
                        # Close the file because Windows won't let open it second time
                        tfile.close()
                        filelist.append(tfile.name)
                        # Delete temporary file when the program finishes
                        atexit.register(os.remove, tfile.name)
                    except (ValueError, URLError) as error:
                        if not kwargs.get('quiet', False):
                            (errno, strerror) = error.args
                        return None
            source = filelist

        if not is_url:
            try:
                inputfile = logfileparser.openlogfile(source)
            except IOError as error:
                if not kwargs.get('quiet', False):
                    (errno, strerror) = error.args
                return None
        else:
            try:
                response = urlopen(source)
                is_stream = True

                # Retrieve filename from URL if possible
                filename = re.findall(r"\w+\.\w+", source.split('/')[-1])
                filename = filename[0] if filename else ""

                inputfile = logfileparser.openlogfile(filename, object=response.read())
            except (ValueError, URLError) as error:
                if not kwargs.get('quiet', False):
                    (errno, strerror) = error.args
                return None

    elif hasattr(source, "read"):
        inputfile = source
        is_stream = True

    # Streams are tricky since they don't have seek methods or seek won't work
    # by design even if it is present. We solve this now by reading in the
    # entire stream and using a StringIO buffer for parsing. This might be
    # problematic for very large streams. Slow streams might also be an issue if
    # the parsing is not instantaneous, but we'll deal with such edge cases
    # as they arise. Ideally, in the future we'll create a class dedicated to
    # dealing with these issues, supporting both files and streams.
    if is_stream:
        try:
            inputfile.seek(0, 0)
        except (AttributeError, IOError):
            contents = inputfile.read()
            try:
                inputfile = io.StringIO(contents)
            except:
                inputfile = io.StringIO(unicode(contents))
            inputfile.seek(0, 0)

    # Proceed to return an instance of the logfile parser only if the filetype
    # could be guessed. Need to make sure the input file is closed before creating
    # an instance, because parsers will handle opening/closing on their own.
    filetype = guess_filetype(inputfile)

    # If the input file isn't a standard compchem log file, try one of
    # the readers, falling back to Open Babel.


    if filetype:
        # We're going to close and reopen below anyway, so this is just to avoid
        # the missing seek method for fileinput.FileInput. In the long run
        # we need to refactor to support for various input types in a more
        # centralized fashion.
        if is_listofstrings:
            pass
        else:
            inputfile.seek(0, 0)
        if not is_stream:
            # if is_listofstrings:
            #     if filetype == Turbomole:
            #         source = sort_turbomole_outputs(source)
            inputfile.close()
            return filetype(source, *args, **kwargs)
        return filetype(inputfile, *args, **kwargs)


def fallback(source):
    """Attempt to read standard molecular formats using other libraries.

    Currently this will read XYZ files with OpenBabel, but this can easily
    be extended to other formats and libraries, too.
    """

    if isinstance(source, str):
        ext = os.path.splitext(source)[1][1:].lower()
        if _has_cclib2openbabel:
            # From OB 3.0 onward, Pybel is contained inside the OB module.
            try:
                import openbabel.pybel as pb
            except:
                import pybel as pb
            if ext in pb.informats:
                return cclib2openbabel.readfile(source, ext)
        else:
            print("Could not import `openbabel`, fallback mechanism might not work.")


def qcwrite(ccobj, outputtype=None, outputdest=None,
            indices=None, terse=False, returnstr=False,
            *args, **kwargs):
    """Write the parsed data from an outputfile to a standard chemical
    representation.

    Inputs:
        ccobj - Either a job (from ccopen) or a data (from job.parse()) object
        outputtype - The output format (should be a string)
        outputdest - A filename or file object for writing
        indices - One or more indices for extracting specific geometries/etc. (zero-based)
        terse -  This option is currently limited to the cjson/json format. Whether to indent the cjson/json or not
        returnstr - Whether or not to return a string representation.

    The different writers may take additional arguments, which are
    documented in their respective docstrings.

    Returns:
        the string representation of the chemical datatype
          requested, or None.
    """

    # Determine the correct output format.
    outputclass = _determine_output_format(outputtype, outputdest)

    # Is ccobj an job object (unparsed), or is it a ccdata object (parsed)?
    if isinstance(ccobj, logfileparser.Logfile):
        jobfilename = ccobj.filename
        ccdata = ccobj.parse()
    elif isinstance(ccobj, data.ccData):
        jobfilename = None
        ccdata = ccobj
    else:
        raise ValueError

    # If the logfile name has been passed in through kwargs (such as
    # in the write script), make sure it has precedence.
    if 'jobfilename' in kwargs:
        jobfilename = kwargs['jobfilename']
        # Avoid passing multiple times into the main call.
        del kwargs['jobfilename']

    outputobj = outputclass(ccdata, jobfilename=jobfilename,
                            indices=indices, terse=terse,
                            *args, **kwargs)
    output = outputobj.generate_repr()

    # If outputdest isn't None, write the output to disk.
    if outputdest is not None:
        if isinstance(outputdest, str):
            with open(outputdest, 'w') as outputobj:
                outputobj.write(output)
        elif isinstance(outputdest, io.IOBase):
            outputdest.write(output)
        else:
            raise ValueError
    # If outputdest is None, return a string representation of the output.
    else:
        return output

    if returnstr:
        return output


def write_champ_old_sym(qcobj, outputdest=None):
    """Writes the parsed geometry, symmetry, determinants, MO coefficients data from the quantum 
    chemistry calculation to old format of champ .sym, .geom, .det, and .lcao file.

    Inputs:
        qcobj - Either a job (from ccopen) or a data (from job.parse()) object
        outputdest - A filename or file object for writing. Example, "rhf.sym", "cn3.sym"

    Returns:
        None as a function value
    """
    # If the output filename is mentioned, then write to that file
    # This will write in the old format that CHAMP recognizes.


    if outputdest is not None:
        if isinstance(outputdest, str):
            ## Write down a symmetry file in old champ format
            with open(outputdest + ".sym", 'w') as file:
                
                values, counts = np.unique(qcobj.mosyms, return_counts=True)                
                # point group symmetry independent line printed below                
                file.write("sym_labels " + str(len(counts)) + " " + str(len(qcobj.mosyms[0]))+"\n")

                irrep_string = ""
                irrep_correspondence = {}
                for i, val in enumerate(values):
                    irrep_correspondence[val] = i+1
                    irrep_string += " " + str(i+1) + " " + str(val)

                if all(irreps in qcobj.mosyms[0] for irreps in values):
                    file.write(f"{irrep_string} \n")   # This defines the rule

                    for item in qcobj.mosyms[0]:
                        for key, val in irrep_correspondence.items():
                            if item == key:
                                file.write(str(val)+" ")
                    file.write("\n")
                file.write("end\n")                
            file.close()

        elif isinstance(outputdest, io.IOBase):
            outputdest.write(output)
        else:
            raise ValueError
    # If outputdest is None, return a string representation of the output.
    else:
        return None


def write_champ_old_geo(qcobj, outputdest=None):
    """Writes the parsed geometry data from the quantum 
    chemistry calculation to old format of champ .geo  file.

    Inputs:
        qcobj - Either a job (from ccopen) or a data (from job.parse()) object
        outputdest - A filename or file object for writing. Example, "rhf.geo", "cn3.geo"

    Returns:
        None as a function value
    """

   
    # If the output filename is mentioned, then write to that file
    # This will write in the old format that CHAMP recognizes.


    if outputdest is not None:
        if isinstance(outputdest, str):
            ## Write down a symmetry file in old champ format
            with open(outputdest + ".geo", 'w') as file:
                
                # header line printed below                
                file.write("# Comments about the system being studied \n")
                file.write("&atoms nctype " + str(len(set(qcobj.atomnos))) + " natom " + str(qcobj.natom) + "\n" )
                

                # Get the list of unique elements of the list and the index of them (note python indenxing starts at 0)
                unique_elements = list(dict.fromkeys(qcobj.atomnos))
                indices = [unique_elements.index(i) for i in qcobj.atomnos]

                element_string = ""
                for i, val in enumerate(unique_elements):
                    element_string += " " + str(i+1) + " " + str(pt.elements[val].symbol)        
                file.write("&atom_types " + element_string + "\n" )                
                file.write("geometry\n")                

                coords = [[qcobj.atomcoords[0][i][j] for j in range(3)] for i in range(len(qcobj.atomnos))]
                coords = np.array(coords)/0.5291772109 #angstrom_to_bohr conversion


                for element in range(len(qcobj.atomnos)):
                    for i in range(3):
                        file.write (f"{coords[element][i]: 0.6f} ")
                    file.write(f" {indices[element]+1} \n") 

#                # Alternate version for better readability
#                for element in range(len(qcobj.atomnos)):
#                    file.write("{: 0.6f} {: 0.6f} {: 0.6f} {} \n".format(coords[element][0], coords[element][1], coords[element][2], indices[element]+1)) 

                file.write("end\n")                
                file.write("znuc\n")                                
                core  = Core()
                for element in unique_elements:
                    file.write("{: 0.6f} ".format(core.valence[element]) ) 

                file.write("\n")                
                file.write("end\n")                
            file.close()

        elif isinstance(outputdest, io.IOBase):
            outputdest.write(output)
        else:
            raise ValueError
    # If outputdest is None, return a string representation of the output.
    else:
        return None


def write_champ_old_lcao(qcobj, outputdest=None):
    """Writes the parsed geometry data from the quantum 
    chemistry calculation to old format of champ .lcao  file.

    Inputs:
        qcobj - Either a job (from ccopen) or a data (from job.parse()) object
        outputdest - A filename or file object for writing. Example, "rhf.lcao", "cn3.lcao"

    Returns:
        None as a function value
    """

   
    # If the output filename is mentioned, then write to that file
    # This will write in the old format that CHAMP recognizes.


    if outputdest is not None:
        if isinstance(outputdest, str):
            ## Write down a symmetry file in old champ format
            with open(outputdest + ".lcao", 'w') as file:
                      
                # header line printed below                
                file.write("# Comments about the system being studied \n")
                file.write("lcao " + str(len(qcobj.mocoeffs[0][0])) + " " + str(len(qcobj.mocoeffs[0][0])) + "\n" )
                np.savetxt(file, qcobj.mocoeffs[0][:])
                file.write("end\n")                
            file.close()

        elif isinstance(outputdest, io.IOBase):
            outputdest.write(output)
        else:
            raise ValueError
    # If outputdest is None, return a string representation of the output.
    else:
        return None


def write_champ_old_det(qcobj, outputdest=None):
    """Writes the parsed determinants data from the quantum 
    chemistry calculation to old format of champ .det file.

    Inputs:
        qcobj - Either a job (from ccopen) or a data (from job.parse()) object
        outputdest - A filename or file object for writing. Example, "rhf.det", "cn3.det"

    Returns:
        None as a function value
    """
    
    # If the output filename is mentioned, then write to that file
    # This will write in the old format that CHAMP recognizes.


    if outputdest is not None:
        if isinstance(outputdest, str):
            ## Write down a symmetry file in old champ format
            with open(outputdest + ".det", 'w') as file:

                if qcobj.scftype in ["RHF", "UHF", "ROHF"]:

                    file.write(f"&electrons  nelec {qcobj.number_alpha_valence+qcobj.number_beta_valence} nup {qcobj.number_alpha_valence} \n" )                
                    file.write(f"\n" ) 
                    file.write(f"determinants {1} {1} \n")
                    file.write(f"      {1:.6f} \n")                                                        

                    alpha_occupation = np.arange(qcobj.number_alpha_valence) + 1
                    beta_occupation  = np.arange(qcobj.number_alpha_valence) + 1                    
                    np.savetxt(file, np.row_stack((alpha_occupation, beta_occupation)), fmt='  %i', delimiter='  ', newline='')
                  
                    file.write("\n")
                    file.write("end\n")                
                    file.close()

                elif qcobj.scftype in ["MCSCF"]:
                    raise Warning("being implemented")

        elif isinstance(outputdest, io.IOBase):
            outputdest.write(output)
        else:
            raise ValueError
    # If outputdest is None, return a string representation of the output.
    else:
        return None





def _determine_output_format(outputtype, outputdest):
    """
    Determine the correct output format.

    Inputs:
      outputtype - a string corresponding to the file type
      outputdest - a filename string or file handle
    Returns:
      outputclass - the class corresponding to the correct output format
    Raises:
      UnknownOutputFormatError for unsupported file writer extensions
    """

    # Priority for determining the correct output format:
    #  1. outputtype
    #  2. outputdest

    outputclass = None
    # First check outputtype.
    if isinstance(outputtype, str):
        extension = outputtype.lower()
        if extension in writerclasses:
            outputclass = writerclasses[extension]
        else:
            raise UnknownOutputFormatError(extension)
    else:
        # Then checkout outputdest.
        if isinstance(outputdest, str):
            extension = os.path.splitext(outputdest)[1].lower()
        elif isinstance(outputdest, io.IOBase):
            extension = os.path.splitext(outputdest.name)[1].lower()
        else:
            raise UnknownOutputFormatError
        if extension in writerclasses:
            outputclass = writerclasses[extension]
        else:
            raise UnknownOutputFormatError(extension)

    return outputclass

def path_leaf(path):
    """
    Splits the path to give the filename. Works irrespective of '\'
    or '/' appearing in the path and also with path ending with '/' or '\'.

    Inputs:
      path - a string path of a logfile.
    Returns:
      tail - 'directory/subdirectory/logfilename' will return 'logfilename'.
      ntpath.basename(head) - 'directory/subdirectory/logfilename/' will return 'logfilename'.
    """
    head, tail = os.path.split(path)
    return tail or os.path.basename(head)

def sort_turbomole_outputs(filelist):
    """
    Sorts a list of inputs (or list of log files) according to the order
    defined below. Just appends the unknown files in the end of the sorted list.

    Inputs:
      filelist - a list of Turbomole log files needed to be parsed.
    Returns:
      sorted_list - a sorted list of Turbomole files needed for proper parsing.
    """
    sorting_order = {
        'basis' : 0,
        'control' : 1,
        'mos' : 2,
        'alpha' : 3,
        'beta' : 4,
        'job.last' : 5,
        'coord' : 6,
        'gradient' : 7,
        'aoforce' : 8,
    }

    known_files = []
    unknown_files = []
    sorted_list = []
    for fname in filelist:
        filename = path_leaf(fname)
        if filename in sorting_order:
            known_files.append([fname, sorting_order[filename]])
        else:
            unknown_files.append(fname)
    for i in sorted(known_files, key=lambda x: x[1]):
        sorted_list.append(i[0])
    if unknown_files:
        sorted_list.extend(unknown_files)
    return sorted_list


def _check_pandas(found_pandas):
    if not found_pandas:
        raise ImportError("You must install `pandas` to use this function")


def ccframe(ccobjs, *args, **kwargs):
    """Returns a pandas.DataFrame of data attributes parsed by cclib from one
    or more logfiles.

    Inputs:
        ccobjs - an iterable of either cclib jobs (from ccopen) or data (from
        job.parse()) objects

    Returns:
        a pandas.DataFrame
    """
    _check_pandas(_has_pandas)
    logfiles = []
    for ccobj in ccobjs:
        # Is ccobj an job object (unparsed), or is it a ccdata object (parsed)?
        if isinstance(ccobj, logfileparser.Logfile):
            jobfilename = ccobj.filename
            ccdata = ccobj.parse()
        elif isinstance(ccobj, data.ccData):
            jobfilename = None
            ccdata = ccobj
        else:
            raise ValueError

        attributes = ccdata.getattributes()
        attributes.update({
            'jobfilename': jobfilename
        })

        logfiles.append(pd.Series(attributes))
    return pd.DataFrame(logfiles)


del find_package
