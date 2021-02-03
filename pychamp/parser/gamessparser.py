# -*- coding: utf-8 -*-
#

"""Parser for GAMESS(US) output files"""


import re

import numpy


from pychamp.parser import logfileparser
from pychamp.parser import utils


class GAMESS(logfileparser.Logfile):
    """A GAMESS log file."""

    # Used to index self.scftargets[].
    SCFRMS, SCFMAX, SCFENERGY = list(range(3))

    # Used to extact Dunning basis set names.
    dunningbas = {'CCD': 'cc-pVDZ', \
            'CCT': 'cc-pVTZ', \
            'CCQ': 'cc-pVQZ', \
            'CC5': 'cc-pV5Z', \
            'CC6': 'cc-pV6Z', \
            'ACCD': 'aug-cc-pVDZ', \
            'ACCT': 'aug-cc-pVTZ', \
            'ACCQ': 'aug-cc-pVQZ', \
            'ACC5': 'aug-cc-pV5Z', \
            'ACC6': 'aug-cc-pV6Z', \
            'CCDC': 'cc-pCVDZ', \
            'CCTC': 'cc-pCVTZ', \
            'CCQC': 'cc-pCVQZ', \
            'CC5C': 'cc-pCV5Z', \
            'CC6C': 'cc-pCV6Z', \
            'ACCDC': 'aug-cc-pCVDZ', \
            'ACCTC': 'aug-cc-pCVTZ', \
            'ACCQC': 'aug-cc-pCVQZ', \
            'ACC5C': 'aug-cc-pCV5Z', \
            'ACC6C': 'aug-cc-pCV6Z'}

    # The following keyword is Used to extact Burkatzki-Filippi-Dolg (BFD) basis set names.
    bfdbasis = {'BFD-D'         : 'VDZ', \
                'BFD-T'         : 'VTZ', \
                'BFD-Tp'        : 'VTZprime', \
                'BFD-Qp'        : 'VQZprime', \
                'BFD-Da'        : 'VDZaug', \
                'BFD-Tpa'       : 'VTZaug', \
                'BFD-Qpa'       : 'VQZaug', \
                'BFD-Tpa_nof'   : 'VTZaugnof', \
                'BFD-Qpa_nof'   : 'VQZaugnof'}



    def __init__(self, *args, **kwargs):

        # Call the __init__ method of the superclass
        super(GAMESS, self).__init__(logname="GAMESS", *args, **kwargs)

    def __str__(self):
        """Return a string representation of the object."""
        return "GAMESS log file %s" % (self.filename)

    def __repr__(self):
        """Return a representation of the object."""
        return 'GAMESS("%s")' % (self.filename)

    def normalisesym(self, label):
        """Normalise the symmetries used by GAMESS.

        To normalise, two rules need to be applied:
        (1) Occurences of U/G in the 2/3 position of the label
            must be lower-cased
        (2) Two single quotation marks must be replaced by a double
        """

        if label[1:] == "''":
            end = '"'
        else:
            end = label[1:].replace("U", "u").replace("G", "g")
        return label[0] + end

    def before_parsing(self):

        self.firststdorient = True  # Used to decide whether to wipe the atomcoords clean
        self.cihamtyp = "none"  # Type of CI Hamiltonian: saps or dets.
        self.scftype = "none"  # Type of SCF calculation: BLYP, RHF, ROHF, etc.

    def extract(self, inputfile, line):
        """Extract information from the file object inputfile."""

        if "GAMESS VERSION =" in line:
            # ...so avoid overwriting it if Firefly already set this field.
            if "package_version" not in self.metadata:
                tokens = line.split()
                day, month, year = tokens[4:7]
                possible_release = tokens[-2]
                # There may not be a (Rn) for the nth release that year, in
                # which case this index is the same as 7 (the year).
                if possible_release == year:
                    release = "1"
                else:
                    # `(R23)` -> 23
                    release = possible_release[2:-1]
                self.metadata["package_version"] = '{}.r{}'.format(year, release)
                self.metadata["legacy_package_version"] = "{}R{}".format(year, release)

        if line[1:12] == "INPUT CARD>":
            return

        # extract the methods
        if line[1:7] == "SCFTYP":
            method = line.split()[0][7:]
            if len(self.metadata["methods"]) == 0:
                self.metadata["methods"].append(method)

        # extract the basis set name
        if line[5:11] == "GBASIS":
            basnm1 = line.split()[0][7:]
            if basnm1 in self.dunningbas:
                self.metadata["basis_set"] = self.dunningbas[basnm1]
            else:
                if basnm1 == "PM3" or basnm1 == "AM1":
                    self.metadata["methods"].append(basnm1)
                if basnm1 == "STO" :
                    if line.split()[2] == "2":
                        self.metadata["basis_set"] = "STO-2G"
                    elif line.split()[2] == "3":
                        self.metadata["basis_set"] = "STO-3G"
                    elif line.split()[2] == "4":
                        self.metadata["basis_set"] = "STO-4G"
                    elif line.split()[2] == "5":
                        self.metadata["basis_set"] = "STO-5G"
                if basnm1 == "N21" :
                    if line.split()[2] == "3" and line.split()[3] == "POLAR=COMMON":
                        self.metadata["basis_set"] = "3-21G*"
                    if line.split()[2] == "3" and line.split()[3] == "POLAR=NONE":
                        self.metadata["basis_set"] = "3-21G"
                    if line.split()[2] == "4" and line.split()[3] == "POLAR=NONE":
                        self.metadata["basis_set"] = "4-21G"
                    if line.split()[2] == "6" and line.split()[3] == "POLAR=NONE":
                        self.metadata["basis_set"] = "6-21G"
                if basnm1 == "N31" :
                    if line.split()[2] == "6" and (line.split()[3] == "POLAR=POPN31" \
                            or line.split()[3] == "POLAR=POPLE"):
                        self.metadata["basis_set"] = "6-31G*"
                        line = next(inputfile)
                        if line.split()[-1] == "T":
                            self.metadata["basis_set"] = "6-31+G*"
                            line = next(inputfile)
                            if line.split()[1] == "0" and line.split()[3] == "T":
                                self.metadata["basis_set"] = "6-31++G*"
                            if line.split()[1] == "1" and line.split()[3] == "T":
                                self.metadata["basis_set"] = "6-31++G**"
                        else:
                            line = next(inputfile)
                            if line.split()[1] == "1":  #NPFUNC = 1
                                self.metadata["basis_set"] = "6-31G**"
                    if line.split()[2] == "6" and line.split()[3] == "POLAR=NONE":
                        self.metadata["basis_set"] = "6-31G"
                    if line.split()[2] == "4" and line.split()[3] == "POLAR=NONE":
                        self.metadata["basis_set"] = "4-31G"
                    if line.split()[2] == "4" and line.split()[3] == "POLAR=POPN31":
                        self.metadata["basis_set"] = "4-31G*"
                if basnm1 == "N311" :
                    if line.split()[2] == "6" and line.split()[3] == "POLAR=POPN311":
                        self.metadata["basis_set"] = "6-311G*"
                        line = next(inputfile)
                        if line.split()[-1] == "T":
                            self.metadata["basis_set"] = "6-311+G*"
                            line = next(inputfile)
                            if line.split()[1] == "0" and line.split()[3] == "T":
                                self.metadata["basis_set"] = "6-311++G*"
                            if line.split()[1] == "1" and line.split()[3] == "T":
                                self.metadata["basis_set"] = "6-311++G**"
                        else:
                            line = next(inputfile)
                            if line.split()[1] == "1":  #NPFUNC = 1
                                self.metadata["basis_set"] = "6-311G**"
                    if line.split()[2] == "6" and line.split()[3] == "POLAR=NONE":
                        self.metadata["basis_set"] = "6-311G"

        # We are looking for this line:
        #           PARAMETERS CONTROLLING GEOMETRY SEARCH ARE
        #           ...
        #           OPTTOL = 1.000E-04          RMIN   = 1.500E-03
        if line[10:18] == "OPTTOL =":
            if not hasattr(self, "geotargets"):
                opttol = float(line.split()[2])
                self.geotargets = numpy.array([opttol, 3. / opttol], "d")

        # Has to deal with such lines as:
        #  FINAL R-B3LYP ENERGY IS     -382.0507446475 AFTER  10 ITERATIONS
        #  FINAL ENERGY IS     -379.7594673378 AFTER   9 ITERATIONS
        # ...so take the number after the "IS"
        if line.find("FINAL") == 1:
            if not hasattr(self, "scfenergies"):
                self.scfenergies = []
            temp = line.split()
####        self.scfenergies.append(utils.convertor(float(temp[temp.index("IS") + 1]), "hartree", "eV"))
            self.scfenergies.append(float(temp[temp.index("IS") + 1]))            
        # Empirical dispersion: first is GAMESS-US, second is Firefly
        if any(
            line.find(dispersion_trigger) == 1
            for dispersion_trigger in (
                    "GRIMME'S DISPERSION ENERGY", "Dispersion correction to total energy"
            )
        ):
            dispersion = utils.convertor(float(line.split()[-1]), "hartree", "eV")
            self.append_attribute("dispersionenergies", dispersion)



        # Extract charge and multiplicity
        if line[1:19] == "CHARGE OF MOLECULE":

            charge = int(round(float(line.split()[-1])))
            self.set_attribute('charge', charge)

            line = next(inputfile)
            mult = int(line.split()[-1])
            self.set_attribute('mult', mult)

        # Electronic transitions (etenergies) for CIS runs and TD-DFT, which
        # have very similar outputs. The outputs EOM look very differentm, though.
        #
        #  ---------------------------------------------------------------------
        #                    CI-SINGLES EXCITATION ENERGIES
        #  STATE       HARTREE        EV      KCAL/MOL       CM-1         NM
        #  ---------------------------------------------------------------------
        #   1A''   0.1677341781     4.5643    105.2548      36813.40     271.64
        #   ...
        if re.match("(CI-SINGLES|TDDFT) EXCITATION ENERGIES", line.strip()):

            if not hasattr(self, "etenergies"):
                self.etenergies = []

            get_etosc = False
            header = next(inputfile).rstrip()
            if header.endswith("OSC. STR."):
                # water_cis_dets.out does not have the oscillator strength
                # in this table...it is extracted from a different section below
                get_etosc = True
                self.etoscs = []

            self.skip_line(inputfile, 'dashes')

            line = next(inputfile)
            broken = line.split()
            while len(broken) > 0:

                # Take hartree value with more numbers, and convert.
                # Note that the values listed after this are also less exact!
                etenergy = float(broken[1])
                self.etenergies.append(utils.convertor(etenergy, "hartree", "wavenumber"))
                if get_etosc:
                    etosc = float(broken[-1])
                    self.etoscs.append(etosc)
                broken = next(inputfile).split()

        # Detect the CI hamiltonian type, if applicable.
        # Should always be detected if CIS is done.
        if line[8:64] == "RESULTS FROM SPIN-ADAPTED ANTISYMMETRIZED PRODUCT (SAPS)":
            self.cihamtyp = "saps"
        if line[8:64] == "RESULTS FROM DETERMINANT BASED ATOMIC ORBITAL CI-SINGLES":
            self.cihamtyp = "dets"

        # etsecs (used only for CIS runs for now)
        if line[1:14] == "EXCITED STATE":
            if not hasattr(self, 'etsecs'):
                self.etsecs = []
            if not hasattr(self, 'etsyms'):
                self.etsyms = []
            statenumber = int(line.split()[2])
            spin = int(float(line.split()[7]))
            if spin == 0:
                sym = "Singlet"
            if spin == 1:
                sym = "Triplet"
            sym += '-' + line.split()[-1]
            self.etsyms.append(sym)
            # skip 5 lines
            for i in range(5):
                line = next(inputfile)
            line = next(inputfile)
            CIScontribs = []
            while line.strip()[0] != "-":
                MOtype = 0
                # alpha/beta are specified for hamtyp=dets
                if self.cihamtyp == "dets":
                    if line.split()[0] == "BETA":
                        MOtype = 1
                fromMO = int(line.split()[-3])-1
                toMO = int(line.split()[-2])-1
                coeff = float(line.split()[-1])
                # With the SAPS hamiltonian, the coefficients are multiplied
                #   by sqrt(2) so that they normalize to 1.
                # With DETS, both alpha and beta excitations are printed.
                # if self.cihamtyp == "saps":
                #    coeff /= numpy.sqrt(2.0)
                CIScontribs.append([(fromMO, MOtype), (toMO, MOtype), coeff])
                line = next(inputfile)
            self.etsecs.append(CIScontribs)

        # etoscs (used only for CIS runs now)
        if line[1:50] == "TRANSITION FROM THE GROUND STATE TO EXCITED STATE":
            if not hasattr(self, "etoscs"):
                self.etoscs = []

            # This was the suggested as a fix in issue #61, and it does allow
            # the parser to finish without crashing. However, it seems that
            # etoscs is shorter in this case than the other transition attributes,
            # so that should be somehow corrected and tested for.
            if "OPTICALLY" in line:
                pass
            else:
                statenumber = int(line.split()[-1])
                # skip 7 lines
                for i in range(8):
                    line = next(inputfile)
                strength = float(line.split()[3])
                self.etoscs.append(strength)

        # TD-DFT for GAMESS-US.
        # The format for excitations has changed a bit between 2007 and 2012.
        # Original format parser was written for:
        #
        #          -------------------
        #          TRIPLET EXCITATIONS
        #          -------------------
        #
        # STATE #   1  ENERGY =    3.027228 EV
        # OSCILLATOR STRENGTH =    0.000000
        #        DRF    COEF       OCC      VIR
        #        ---    ----       ---      ---
        #         35 -1.105383     35  ->   36
        #         69 -0.389181     34  ->   37
        #        103 -0.405078     33  ->   38
        #        137  0.252485     32  ->   39
        #        168 -0.158406     28  ->   40
        #
        # STATE #   2  ENERGY =    4.227763 EV
        # ...
        #
        # Here is the corresponding 2012 version:
        #
        #          -------------------
        #          TRIPLET EXCITATIONS
        #          -------------------
        #
        # STATE #   1  ENERGY =    3.027297 EV
        # OSCILLATOR STRENGTH =    0.000000
        # LAMBDA DIAGNOSTIC   =    0.925 (RYDBERG/CHARGE TRANSFER CHARACTER)
        # SYMMETRY OF STATE   =    A
        #                 EXCITATION  DE-EXCITATION
        #     OCC     VIR  AMPLITUDE      AMPLITUDE
        #      I       A     X(I->A)        Y(A->I)
        #     ---     ---   --------       --------
        #     35      36   -0.929190      -0.176167
        #     34      37   -0.279823      -0.109414
        # ...
        #
        # We discern these two by the presence of the arrow in the old version.
        #
        # The "LET EXCITATIONS" pattern used below catches both
        # singlet and triplet excitations output.
        if line[14:29] == "LET EXCITATIONS":

            self.etenergies = []
            self.etoscs = []
            self.etsecs = []
            etsyms = []

            self.skip_lines(inputfile, ['d', 'b'])

            # Loop while states are still being printed.
            line = next(inputfile)
            while line[1:6] == "STATE":

                self.updateprogress(inputfile, "Excited States")

                etenergy = utils.convertor(float(line.split()[-2]), "eV", "wavenumber")
                etoscs = float(next(inputfile).split()[-1])
                self.etenergies.append(etenergy)
                self.etoscs.append(etoscs)

                # Symmetry is not always present, especially in old versions.
                # Newer versions, on the other hand, can also provide a line
                # with lambda diagnostic and some extra headers.
                line = next(inputfile)
                if "LAMBDA DIAGNOSTIC" in line:
                    line = next(inputfile)
                if "SYMMETRY" in line:
                    etsyms.append(line.split()[-1])
                    line = next(inputfile)
                if "EXCITATION" in line and "DE-EXCITATION" in line:
                    line = next(inputfile)
                if line.count("AMPLITUDE") == 2:
                    line = next(inputfile)

                self.skip_line(inputfile, 'dashes')

                CIScontribs = []
                line = next(inputfile)
                while line.strip():
                    cols = line.split()
                    if "->" in line:
                        i_occ_vir = [2, 4]
                        i_coeff = 1

                    else:
                        i_occ_vir = [0, 1]
                        i_coeff = 2
                    fromMO, toMO = [int(cols[i]) - 1 for i in i_occ_vir]
                    coeff = float(cols[i_coeff])
                    CIScontribs.append([(fromMO, 0), (toMO, 0), coeff])
                    line = next(inputfile)
                self.etsecs.append(CIScontribs)
                line = next(inputfile)

            # The symmetries are not always present.
            if etsyms:
                self.etsyms = etsyms

        # # Maximum and RMS gradients.
        # if "MAXIMUM GRADIENT" in line or "RMS GRADIENT" in line:

        #     parts = line.split()

        #     # Avoid parsing the following...

        #     ## YOU SHOULD RESTART "OPTIMIZE" RUNS WITH THE COORDINATES
        #     ## WHOSE ENERGY IS LOWEST.  RESTART "SADPOINT" RUNS WITH THE
        #     ## COORDINATES WHOSE RMS GRADIENT IS SMALLEST.  THESE ARE NOT
        #     ## ALWAYS THE LAST POINT COMPUTED!

        #     if parts[0] not in ["MAXIMUM", "RMS", "(1)"]:
        #         return

        #     if not hasattr(self, "geovalues"):
        #         self.geovalues = []

        #     # Newer versions (around 2006) have both maximum and RMS on one line:
        #     #       MAXIMUM GRADIENT =  0.0531540    RMS GRADIENT = 0.0189223
        #     if len(parts) == 8:
        #         maximum = float(parts[3])
        #         rms = float(parts[7])

        #     # In older versions of GAMESS, this spanned two lines, like this:
        #     #       MAXIMUM GRADIENT =    0.057578167
        #     #           RMS GRADIENT =    0.027589766
        #     if len(parts) == 4:
        #         maximum = float(parts[3])
        #         line = next(inputfile)
        #         parts = line.split()
        #         rms = float(parts[3])

        #     # FMO also prints two final one- and two-body gradients (see exam37):
        #     #   (1) MAXIMUM GRADIENT =  0.0531540    RMS GRADIENT = 0.0189223
        #     if len(parts) == 9:
        #         maximum = float(parts[4])
        #         rms = float(parts[8])

        #     self.geovalues.append([maximum, rms])

        # This is the input orientation, which is the only data available for
        # SP calcs, but which should be overwritten by the standard orientation
        # values, which is the only information available for all geoopt cycles.
        if line[11:50] == "ATOMIC                      COORDINATES":

            if not hasattr(self, "atomcoords"):
                self.atomcoords = []

            line = next(inputfile)
            atomcoords = []
            atomnos = []
            line = next(inputfile)
            while line.strip():
                temp = line.strip().split()
                atomcoords.append([utils.convertor(float(x), "bohr", "Angstrom") for x in temp[2:5]])
                atomnos.append(int(round(float(temp[1]))))  # Don't use the atom name as this is arbitary
                line = next(inputfile)

            self.set_attribute('atomnos', atomnos)
            self.atomcoords.append(atomcoords)

        if line[12:40] == "EQUILIBRIUM GEOMETRY LOCATED":
            # Prevent extraction of the final geometry twice
            if not hasattr(self, 'optdone'):
                self.optdone = []
            self.optdone.append(len(self.geovalues) - 1)

        # Make sure we always have optdone for geomtry optimization, even if not converged.
        if "GEOMETRY SEARCH IS NOT CONVERGED" in line:
            if not hasattr(self, 'optdone'):
                self.optdone = []

        # This is the standard orientation, which is the only coordinate
        # information available for all geometry optimisation cycles.
        # The input orientation will be overwritten if this is a geometry optimisation
        # We assume that a previous Input Orientation has been found and
        # used to extract the atomnos
        if line[1:29] == "COORDINATES OF ALL ATOMS ARE" and (not hasattr(self, "optdone") or self.optdone == []):

            self.updateprogress(inputfile, "Coordinates")

            if self.firststdorient:
                self.firststdorient = False
                # Wipes out the single input coordinate at the start of the file
                self.atomcoords = []

            self.skip_lines(inputfile, ['line', '-'])

            atomcoords = []
            line = next(inputfile)

            for i in range(self.natom):
                temp = line.strip().split()
                atomcoords.append(list(map(float, temp[2:5])))
                line = next(inputfile)
            self.atomcoords.append(atomcoords)

        # Section with SCF information.
        #
        # The space at the start of the search string is to differentiate from MCSCF.
        # Everything before the search string is stored as the type of SCF.
        # SCF types may include: BLYP, RHF, ROHF, UHF, etc.
        #
        # For example, in exam17 the section looks like this (note that this is GVB):
        #          ------------------------
        #          ROHF-GVB SCF CALCULATION
        #          ------------------------
        # GVB STEP WILL USE    119875 WORDS OF MEMORY.
        #
        #     MAXIT=  30   NPUNCH= 2   SQCDF TOL=1.0000E-05
        #     NUCLEAR ENERGY=        6.1597411978
        #     EXTRAP=T   DAMP=F   SHIFT=F   RSTRCT=F   DIIS=F  SOSCF=F
        #
        # ITER EX     TOTAL ENERGY       E CHANGE        SQCDF       DIIS ERROR
        #   0  0      -38.298939963   -38.298939963   0.131784454   0.000000000
        #   1  1      -38.332044339    -0.033104376   0.026019716   0.000000000
        # ... and will be terminated by a blank line.
        if line.rstrip()[-16:] == " SCF CALCULATION":

            # Remember the type of SCF.
            self.scftype = line.strip()[:-16]

            self.skip_line(inputfile, 'dashes')

            while line[:5] != " ITER":

                self.updateprogress(inputfile, "Attributes")

                # GVB uses SQCDF for checking convergence (for example in exam17).
                if "GVB" in self.scftype and "SQCDF TOL=" in line:
                    scftarget = float(line.split("=")[-1])

                # Normally, however, the density is used as the convergence criterium.
                # Deal with various versions:
                #   (GAMESS VERSION = 12 DEC 2003)
                #     DENSITY MATRIX CONV=  2.00E-05  DFT GRID SWITCH THRESHOLD=  3.00E-04
                #   (GAMESS VERSION = 22 FEB 2006)
                #     DENSITY MATRIX CONV=  1.00E-05
                #   (PC GAMESS version 6.2, Not DFT?)
                #     DENSITY CONV=  1.00E-05
                elif "DENSITY CONV" in line or "DENSITY MATRIX CONV" in line:
                    scftarget = float(line.split()[-1])

                line = next(inputfile)

            if not hasattr(self, "scftargets"):
                self.scftargets = []

            self.scftargets.append([scftarget])

            if not hasattr(self, "scfvalues"):
                self.scfvalues = []

            # Normally the iterations print in 6 columns.
            # For ROHF, however, it is 5 columns, thus this extra parameter.
            if "ROHF" in self.scftype:
                self.scf_valcol = 4
            else:
                self.scf_valcol = 5

            line = next(inputfile)

            # SCF iterations are terminated by a blank line.
            # The first four characters usually contains the step number.
            # However, lines can also contain messages, including:
            #   * * *   INITIATING DIIS PROCEDURE   * * *
            #   CONVERGED TO SWOFF, SO DFT CALCULATION IS NOW SWITCHED ON
            #   DFT CODE IS SWITCHING BACK TO THE FINER GRID
            values = []
            while line.strip():
                try:
                    temp = int(line[0:4])
                except ValueError:
                    pass
                else:
                    # if there were 100 iterations or more, the first part of the line
                    # will look like 10099, 101100, 102101, etc., with no spaces between
                    # the numbers. We can check if this is the case by seeing if the first
                    # number on the line exceeds 10000.
                    split_line = [line[0:4], line[4:7]] + line[7:].split()
                    values.append([float(split_line[self.scf_valcol])])
                try:
                    line = next(inputfile)
                except StopIteration:
                    self.logger.warning('File terminated before end of last SCF!')
                    break
            self.scfvalues.append(values)


        # Sometimes, only the first SCF cycle has the banner parsed for above,
        # so we must identify them from the header before the SCF iterations.
        # The example we have for this is the GeoOpt unittest for Firefly8.
        if line[1:8] == "ITER EX":

            # In this case, the convergence targets are not printed, so we assume
            # they do not change.
            self.scftargets.append(self.scftargets[-1])

            values = []
            line = next(inputfile)
            while line.strip():
                try:
                    temp = int(line[0:4])
                except ValueError:
                    pass
                else:
                    values.append([float(line.split()[self.scf_valcol])])
                line = next(inputfile)
            self.scfvalues.append(values)



        if line[5:21] == "ATOMIC BASIS SET":
            self.gbasis = []
            line = next(inputfile)
            while line.find("SHELL") < 0:
                line = next(inputfile)

            self.skip_lines(inputfile, ['blank', 'atomname'])

            # shellcounter stores the shell no of the last shell
            # in the previous set of primitives
            shellcounter = 1
            while line.find("TOTAL NUMBER") < 0:

                self.skip_line(inputfile, 'blank')

                line = next(inputfile)
                shellno = int(line.split()[0])
                shellgap = shellno - shellcounter
                gbasis = []  # Stores basis sets on one atom
                shellsize = 0
                while len(line.split()) != 1 and line.find("TOTAL NUMBER") < 0:
                    shellsize += 1
                    coeff = {}
                    # coefficients and symmetries for a block of rows
                    while line.strip():
                        temp = line.strip().split()
                        sym = temp[1]
                        assert sym in ['S', 'P', 'D', 'F', 'G', 'L']
                        if sym == "L":  # L refers to SP
                            if len(temp) == 6:  # GAMESS US
                                coeff.setdefault("S", []).append((float(temp[3]), float(temp[4])))
                                coeff.setdefault("P", []).append((float(temp[3]), float(temp[5])))
                            else:  # PC GAMESS
                                assert temp[6][-1] == temp[9][-1] == ')'
                                coeff.setdefault("S", []).append((float(temp[3]), float(temp[6][:-1])))
                                coeff.setdefault("P", []).append((float(temp[3]), float(temp[9][:-1])))
                        else:
                            if len(temp) == 5:  # GAMESS US
                                coeff.setdefault(sym, []).append((float(temp[3]), float(temp[4])))
                            else:  # PC GAMESS
                                assert temp[6][-1] == ')'
                                coeff.setdefault(sym, []).append((float(temp[3]), float(temp[6][:-1])))
                        line = next(inputfile)
                    # either a blank or a continuation of the block
                    if sym == "L":
                        gbasis.append(('S', coeff['S']))
                        gbasis.append(('P', coeff['P']))
                    else:
                        gbasis.append((sym, coeff[sym]))
                    line = next(inputfile)
                # either the start of the next block or the start of a new atom or
                # the end of the basis function section

                numtoadd = 1 + (shellgap // shellsize)
                shellcounter = shellno + shellsize
                for x in range(numtoadd):
                    self.gbasis.append(gbasis)

        # The eigenvectors, which also include MO energies and symmetries, follow
        # the *final* report of evalues and the last list of symmetries in the log file:
        #
        #           ------------
        #           EIGENVECTORS
        #           ------------
        #
        #                       1          2          3          4          5
        #                   -10.0162   -10.0161   -10.0039   -10.0039   -10.0029
        #                      BU         AG         BU         AG         AG
        #     1  C  1  S    0.699293   0.699290  -0.027566   0.027799   0.002412
        #     2  C  1  S    0.031569   0.031361   0.004097  -0.004054  -0.000605
        #     3  C  1  X    0.000908   0.000632  -0.004163   0.004132   0.000619
        #     4  C  1  Y   -0.000019   0.000033   0.000668  -0.000651   0.005256
        #     5  C  1  Z    0.000000   0.000000   0.000000   0.000000   0.000000
        #     6  C  2  S   -0.699293   0.699290   0.027566   0.027799   0.002412
        #     7  C  2  S   -0.031569   0.031361  -0.004097  -0.004054  -0.000605
        #     8  C  2  X    0.000908  -0.000632  -0.004163  -0.004132  -0.000619
        #     9  C  2  Y   -0.000019  -0.000033   0.000668   0.000651  -0.005256
        #    10  C  2  Z    0.000000   0.000000   0.000000   0.000000   0.000000
        #    11  C  3  S   -0.018967  -0.019439   0.011799  -0.014884  -0.452328
        #    12  C  3  S   -0.007748  -0.006932   0.000680  -0.000695  -0.024917
        #    13  C  3  X    0.002628   0.002997   0.000018   0.000061  -0.003608
        # ...
        #
        # There are blanks lines between each block.
        #
        # Warning! There are subtle differences between GAMESS-US and PC-GAMES
        # in the formatting of the first four columns. In particular, for F orbitals,
        # PC GAMESS:
        #   19  C   1 YZ   0.000000   0.000000   0.000000   0.000000   0.000000
        #   20  C    XXX   0.000000   0.000000   0.000000   0.000000   0.002249
        #   21  C    YYY   0.000000   0.000000  -0.025555   0.000000   0.000000
        #   22  C    ZZZ   0.000000   0.000000   0.000000   0.002249   0.000000
        #   23  C    XXY   0.000000   0.000000   0.001343   0.000000   0.000000
        # GAMESS US
        #   55  C  1 XYZ   0.000000   0.000000   0.000000   0.000000   0.000000
        #   56  C  1XXXX  -0.000014  -0.000067   0.000000   0.000000   0.000000
        #
        if line.find("EIGENVECTORS") == 10 or line.find("MOLECULAR ORBITALS") == 10:

            # This is the stuff that we can read from these blocks.
            self.moenergies = [[]]
            self.mosyms = [[]]

            if not hasattr(self, "nmo"):
                self.nmo = self.nbasis

            self.mocoeffs = [numpy.zeros((self.nmo, self.nbasis), "d")]

            readatombasis = False
            if not hasattr(self, "atombasis"):
                self.atombasis = []
                self.aonames = []
                for i in range(self.natom):
                    self.atombasis.append([])
                self.aonames = []
                readatombasis = True

            self.skip_line(inputfile, 'dashes')

            for base in range(0, self.nmo, 5):
                self.updateprogress(inputfile, "Coefficients")

                line = next(inputfile)

                # This makes sure that this section does not end prematurely,
                # which happens in regression 2CO.ccsd.aug-cc-pVDZ.out.
                if line.strip() != "":
                    break

                numbers = next(inputfile)  # Eigenvector numbers.

                # This is for regression CdtetraM1B3LYP.
                if "ALPHA SET" in numbers:
                    blank = next(inputfile)
                    numbers = next(inputfile)

                # If not all coefficients are printed, the logfile will go right to
                # the beta section if there is one, so break out in that case.
                if "BETA SET" in numbers:
                    line = numbers
                    break

                # Sometimes there are some blank lines here.
                while not line.strip():
                    line = next(inputfile)

                # Geometry optimizations don't have END OF RHF/DFT
                # CALCULATION, they head right into the next section.
                if "--------" in line:
                    break

                # Eigenvalues for these orbitals (in hartrees).
                try:
####                self.moenergies[0].extend([utils.convertor(float(x), "hartree", "eV") for x in line.split()])
                    self.moenergies[0].extend([float(x) for x in line.split()])
                except:
                    self.logger.warning('MO section found but could not be parsed!')
                    break

                # Orbital symmetries.
                line = next(inputfile)
                if line.strip():
                    self.mosyms[0].extend(list(map(self.normalisesym, line.split())))

                # Now we have nbasis lines. We will use the same method as in normalise_aonames() before.
                p = re.compile(r"(\d+)\s*([A-Z][A-Z]?)\s*(\d+)\s*([A-Z]+)")
                oldatom = '0'
                i_atom = 0  # counter to keep track of n_atoms > 99
                flag_w = True  # flag necessary to keep from adding 100's at wrong time

                for i in range(self.nbasis):
                    line = next(inputfile)

                    # If line is empty, break (ex. for FMO in exam37 which is a regression).
                    if not line.strip():
                        break

                    # Fill atombasis and aonames only first time around
                    if readatombasis and base == 0:

                        aonames = []
                        start = line[:17].strip()
                        m = p.search(start)

                        if m:
                            g = m.groups()
                            g2 = int(g[2])  # atom index in GAMESS file; changes to 0 after 99

                            # Check if we have moved to a hundred
                            # if so, increment the counter and add it to the parsed value
                            # There will be subsequent 0's as that atoms AO's are parsed
                            # so wait until the next atom is parsed before resetting flag
                            if g2 == 0 and flag_w:
                                i_atom = i_atom + 100
                                flag_w = False  # handle subsequent AO's
                            if g2 != 0:
                                flag_w = True  # reset flag
                            g2 = g2 + i_atom

                            aoname = "%s%i_%s" % (g[1].capitalize(), g2, g[3])
                            oldatom = str(g2)
                            atomno = g2-1
                            orbno = int(g[0])-1
                        else:  # For F orbitals, as shown above
                            g = [x.strip() for x in line.split()]
                            aoname = "%s%s_%s" % (g[1].capitalize(), oldatom, g[2])
                            atomno = int(oldatom)-1
                            orbno = int(g[0])-1

                        self.atombasis[atomno].append(orbno)
                        self.aonames.append(aoname)

                    coeffs = line[15:]  # Strip off the crud at the start.
                    j = 0
                    while j*11+4 < len(coeffs):
                        self.mocoeffs[0][base+j, i] = float(coeffs[j * 11:(j + 1) * 11])
                        j += 1

            # If it's a restricted calc and no more properties, we have:
            #
            #  ...... END OF RHF/DFT CALCULATION ......
            #
            # If there are more properties (such as the density matrix):
            #               --------------
            #
            # If it's an unrestricted calculation, however, we now get the beta orbitals:
            #
            #  ----- BETA SET -----
            #
            #          ------------
            #          EIGENVECTORS
            #          ------------
            #
            #                      1          2          3          4          5
            # ...
            #
            if "BETA SET" not in line:
                line = next(inputfile)
                line = next(inputfile)

            # This can come in between the alpha and beta orbitals (see #130).
            if line.strip() == "LZ VALUE ANALYSIS FOR THE MOS":
                while line.strip():
                    line = next(inputfile)
                line = next(inputfile)

            # Covers label with both dashes and stars (like regression CdtetraM1B3LYP).
            if "BETA SET" in line:
                self.mocoeffs.append(numpy.zeros((self.nmo, self.nbasis), "d"))
                self.moenergies.append([])
                self.mosyms.append([])
                blank = next(inputfile)
                line = next(inputfile)

                # Sometimes EIGENVECTORS is missing, so rely on dashes to signal it.
                if set(line.strip()) == {'-'}:
                    self.skip_lines(inputfile, ['EIGENVECTORS', 'd', 'b'])
                    line = next(inputfile)

                for base in range(0, self.nmo, 5):
                    self.updateprogress(inputfile, "Coefficients")
                    if base != 0:
                        line = next(inputfile)
                        line = next(inputfile)
                    line = next(inputfile)
                    if "properties" in line.lower():
                        break
###                 self.moenergies[1].extend([utils.convertor(float(x), "hartree", "eV") for x in line.split()])
                    self.moenergies[1].extend([float(x) for x in line.split()])                    
                    line = next(inputfile)
                    self.mosyms[1].extend(list(map(self.normalisesym, line.split())))
                    for i in range(self.nbasis):
                        line = next(inputfile)
                        temp = line[15:]  # Strip off the crud at the start
                        j = 0
                        while j * 11 + 4 < len(temp):
                            self.mocoeffs[1][base+j, i] = float(temp[j * 11:(j + 1) * 11])
                            j += 1
                line = next(inputfile)
            self.moenergies = [numpy.array(x, "d") for x in self.moenergies]


        # We cannot trust this self.homos until we come to the phrase:
        #   SYMMETRIES FOR INITAL GUESS ORBITALS FOLLOW
        # which either is followed by "ALPHA" or "BOTH" at which point we can say
        # for certain that it is an un/restricted calculations.
        # Note that MCSCF calcs also print this search string, so make sure
        #   that self.homos does not exist yet.
        if line[1:28] == "NUMBER OF OCCUPIED ORBITALS" and not hasattr(self, 'homos'):

            homos = [int(line.split()[-1])-1]
            line = next(inputfile)
            homos.append(int(line.split()[-1])-1)

            self.set_attribute('homos', homos)

        if line.find("SYMMETRIES FOR INITIAL GUESS ORBITALS FOLLOW") >= 0:
            # Not unrestricted, so lop off the second index.
            # In case the search string above was not used (ex. FMO in exam38),
            #   we can try to use the next line which should also contain the
            #   number of occupied orbitals.
            if line.find("BOTH SET(S)") >= 0:
                nextline = next(inputfile)
                if "ORBITALS ARE OCCUPIED" in nextline:
                    homos = int(nextline.split()[0])-1
                    if hasattr(self, "homos"):
                        try:
                            assert self.homos[0] == homos
                        except AssertionError:
                            self.logger.warning("Number of occupied orbitals not consistent. This is normal for ECP and FMO jobs.")
                    else:
                        self.homos = [homos]
                self.homos = numpy.resize(self.homos, [1])

        # Set the total number of atoms, only once.
        # Normally GAMESS print TOTAL NUMBER OF ATOMS, however in some cases
        #   this is slightly different (ex. lower case for FMO in exam37).
        if not hasattr(self, "natom") and "NUMBER OF ATOMS" in line.upper():
            natom = int(line.split()[-1])
            self.set_attribute('natom', natom)

        # The first is from Julien's Example and the second is from Alexander's
        # I think it happens if you use a polar basis function instead of a cartesian one
        if line.find("NUMBER OF CARTESIAN GAUSSIAN BASIS") == 1 or line.find("TOTAL NUMBER OF BASIS FUNCTIONS") == 1:
            nbasis = int(line.strip().split()[-1])
            self.set_attribute('nbasis', nbasis)

        elif line.find("TOTAL NUMBER OF CONTAMINANTS DROPPED") >= 0:
            nmos_dropped = int(line.split()[-1])
            if hasattr(self, "nmo"):
                self.set_attribute('nmo', self.nmo - nmos_dropped)
            else:
                self.set_attribute('nmo', self.nbasis - nmos_dropped)

        # Note that this line is present if ISPHER=1, e.g. for C_bigbasis
        elif line.find("SPHERICAL HARMONICS KEPT IN THE VARIATION SPACE") >= 0:
            nmo = int(line.strip().split()[-1])
            self.set_attribute('nmo', nmo)

        # Note that this line is not always present, so by default
        # NBsUse is set equal to NBasis (see below).
        elif line.find("TOTAL NUMBER OF MOS IN VARIATION SPACE") == 1:
            nmo = int(line.split()[-1])
            self.set_attribute('nmo', nmo)

        elif line.find("OVERLAP MATRIX") == 0 or line.find("OVERLAP MATRIX") == 1:
            # The first is for PC-GAMESS, the second for GAMESS
            # Read 1-electron overlap matrix
            if not hasattr(self, "aooverlaps"):
                self.aooverlaps = numpy.zeros((self.nbasis, self.nbasis), "d")
            else:
                self.logger.info("Reading additional aooverlaps...")
            base = 0
            while base < self.nbasis:
                self.updateprogress(inputfile, "Overlap")

                self.skip_lines(inputfile, ['b', 'basis_fn_number', 'b'])

                for i in range(self.nbasis - base):  # Fewer lines each time
                    line = next(inputfile)
                    temp = line.split()
                    for j in range(4, len(temp)):
                        self.aooverlaps[base+j-4, i+base] = float(temp[j])
                        self.aooverlaps[i+base, base+j-4] = float(temp[j])
                base += 5

        # ECP Pseudopotential information
        if "ECP POTENTIALS" in line:
            if not hasattr(self, "coreelectrons"):
                self.coreelectrons = [0]*self.natom

            self.skip_lines(inputfile, ['d', 'b'])

            header = next(inputfile)
            while header.split()[0] == "PARAMETERS":
                name = header[17:25]
                atomnum = int(header[34:40])
                # The pseudopotnetial is given explicitely
                if header[40:50] == "WITH ZCORE":
                    zcore = int(header[50:55])
                    lmax = int(header[63:67])
                    self.coreelectrons[atomnum-1] = zcore
                # The pseudopotnetial is copied from another atom
                if header[40:55] == "ARE THE SAME AS":
                    atomcopy = int(header[60:])
                    self.coreelectrons[atomnum-1] = self.coreelectrons[atomcopy-1]
                line = next(inputfile)
                while line.split() != []:
                    line = next(inputfile)
                header = next(inputfile)



        if line[:30] == ' ddikick.x: exited gracefully.'\
                or line[:40] == ' EXECUTION OF GAMESS TERMINATED NORMALLY':
            self.metadata['success'] = True
