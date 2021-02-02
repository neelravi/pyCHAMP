import numpy as np


class Parser:

    # init method or constructor    
    def __init__(self):   
        self.inputfile = "piece.txt"  #"cn3_rhf_BFD-Da.out"
        self.metadata = dict()
        self.nmo = 0
        self.nbasis  = 0       
        self.natom = 0        


    def skip_lines(self, inputfile, sequence):
        """Read trivial line types and check they are what they are supposed to be.

        This function will read len(sequence) lines and do certain checks on them,
        when the elements of sequence have the appropriate values. Currently the
        following elements trigger checks:
            'blank' or 'b'      - the line should be blank
            'dashes' or 'd'     - the line should contain only dashes (or spaces)
            'equals' or 'e'     - the line should contain only equal signs (or spaces)
            'stars' or 's'      - the line should contain only stars (or spaces)
        """

        expected_characters = {
            '-': ['dashes', 'd'],
            '=': ['equals', 'e'],
            '*': ['stars', 's'],
        }

        lines = []
        for expected in sequence:

            # Read the line we want to skip.
            #line = next(inputfile)

            # Blank lines are perhaps the most common thing we want to check for.
            # if expected in ["blank", "b"]:
            #     try:
            #         assert line.strip() == ""
            #     except AssertionError:
            #         frame, fname, lno, funcname, funcline, index = inspect.getouterframes(inspect.currentframe())[1]
            #         parser = fname.split('/')[-1]
            #         msg = "In %s, line %i, line not blank as expected: %s" % (parser, lno, line.strip())
            #         self.logger.warning(msg)

            # All cases of heterogeneous lines can be dealt with by the same code.
            # for character, keys in expected_characters.items():
            #     if expected in keys:
            #         try:
            #             assert all([c == character for c in line.strip() if c != ' '])
            #         except AssertionError:
            #             frame, fname, lno, funcname, funcline, index = inspect.getouterframes(inspect.currentframe())[1]
            #             parser = fname.split('/')[-1]
            #             msg = "In %s, line %i, line not all %s as expected: %s" % (parser, lno, keys[0], line.strip())
            #             self.logger.warning(msg)
            #             continue

            # Save the skipped line, and we will return the whole list.
            lines.append(line)

        return lines

    skip_line = lambda self, inputfile, expected: self.skip_lines(inputfile, [expected])

    def extract(self, inputfile, line):
        """Extract information from the file object inputfile."""

        # Extract the version number from the log file

        if "GAMESS VERSION =" in line:
            # ...so avoid overwriting it if it is already set this field.
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
#                self.metadata["package_version"] = '{}.r{}'.format(year, release)
#                self.metadata["legacy_package_version"] = "{}R{}".format(year, release)
                print ("version release date {} {} {} {}" .format(day, month, year, release))

#        if line[1:12] == "INPUT CARD>":
#            return

        # extract the methods
        if "SCFTYPE" in line:
            method = line.split()[0][7:]
            print ("calculation type {} ".format(method))            
# uncomment these lines after success
#            if len(self.metadata["methods"]) == 0:
#                self.metadata["methods"].append(method)

### try to read the number of atomic orbitals and number of basis functions



        if line[1:28] == "NUMBER OF OCCUPIED ORBITALS" and not hasattr(self, 'homos'):
            print ("number of occupied orbitals", line)
            homos = [int(line.split()[-1])-1]
            #line = next(inputfile)  # uncomment his
            homos.append(int(line.split()[-1])-1)
            print ("homos", homos)
            #self.set_attribute('homos', homos)

        # if line.find("SYMMETRIES FOR INITIAL GUESS ORBITALS FOLLOW") >= 0:
        #     # Not unrestricted, so lop off the second index.
        #     # In case the search string above was not used (ex. FMO in exam38),
        #     #   we can try to use the next line which should also contain the
        #     #   number of occupied orbitals.
        #     if line.find("BOTH SET(S)") >= 0:
        #         nextline = next(inputfile)
        #         if "ORBITALS ARE OCCUPIED" in nextline:
        #             homos = int(nextline.split()[0])-1
        #             if hasattr(self, "homos"):
        #                 try:
        #                     assert self.homos[0] == homos
        #                 except AssertionError:
        #                     self.logger.warning("Number of occupied orbitals not consistent. This is normal for ECP and FMO jobs.")
        #             else:
        #                 self.homos = [homos]
        #         self.homos = np.resize(self.homos, [1])

        # Set the total number of atoms, only once.
        # Normally GAMESS print TOTAL NUMBER OF ATOMS, however in some cases
        #   this is slightly different (ex. lower case for FMO in exam37).
        if not hasattr(self, "natom") and "NUMBER OF ATOMS" in line.upper():
            natom = int(line.split()[-1])
            self.natom = natom
            print ("Number of atoms ", self.natom)            
            #self.set_attribute('natom', natom)

        # The first is from Julien's Example and the second is from Alexander's
        # I think it happens if you use a polar basis function instead of a cartesian one
        if line.find("NUMBER OF CARTESIAN GAUSSIAN BASIS") == 1 or line.find("TOTAL NUMBER OF BASIS FUNCTIONS") == 1:
            nbasis = int(line.strip().split()[-1])
            self.nbasis = nbasis
            print ("number of cartesian basis", self.nbasis)
            #self.set_attribute('nbasis', nbasis)

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



        if line.find("EIGENVECTORS") == 10 or line.find("MOLECULAR ORBITALS") == 10:

            # This is the stuff that we can read from these blocks.
            self.moenergies = [[]]
            self.mosyms = [[]]

            if not hasattr(self, "nmo"):
                self.nmo = self.nbasis

            self.mocoeffs = [np.zeros((self.nmo, self.nbasis), "d")]
            print ("mocoeff shape", self.mocoeffs)

            readatombasis = False
            # if not hasattr(self, "atombasis"):
            #     self.atombasis = []
            #     self.aonames = []
            #     for i in range(self.natom):
            #         self.atombasis.append([])
            #     self.aonames = []
            #     readatombasis = True

            #self.skip_line(inputfile, 'dashes')
            self.nmo = self.nbasis
            print ("self.nmo", self.nmo)

            for base in range(0, self.nmo, 5):
                print (" in the block of reading vectors")
#                self.updateprogress(inputfile, "Coefficients")
                print (line)

            print ([next(inputfile) for x in range(self.nmo)] )


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
                self.moenergies[0].extend([utils.convertor(float(x), "hartree", "eV") for x in line.split()])
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




gamessparser=Parser()
with open(gamessparser.inputfile) as f:
    lines = f.readlines()
    for line in lines:
        gamessparser.extract(gamessparser, line)
