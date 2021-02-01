class Parser:

    # init method or constructor    
    def __init__(self):   
        self.inputfile = "piece.txt"  #"cn3_rhf_BFD-Da.out"
        self.metadata = dict()

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
        if line[1:7] == "SCFTYP":
            method = line.split()[0][7:]
            print ("calculation type {} ".format(method))            
# uncomment these lines after success
#            if len(self.metadata["methods"]) == 0:
#                self.metadata["methods"].append(method)

        # extract whether doing pseudopotential calculations
        if line.strip()[0:4] == "ECP":
            print (line)
            ecpmethod = line.split()[0][4:]
            print ("whether pseudopotential is read {} ".format(ecpmethod))            
# uncomment these lines after success
#            if len(self.metadata["methods"]) == 0:
#                self.metadata["methods"].append(method)



        # extract the basis set name
        if line[5:11] == "GBASIS":
            basis_name = line.split()[0][7:]
            print ("basis name {} ".format(basis_name))            
            if basis_name in self.dunningbas:
                print ("basis name {} ".format(basis_name))            
# uncomment this lines after success
#                self.metadata["basis_set"] = self.dunningbas[basis_name]
            else:
                if basis_name[0:3] == "BFD-Da":
                    print ("basis name {} ".format(basis_name))            
# uncomment this lines after success
                    # Put the basis set fullaname in the metadata list
#                    self.metadata["methods"].append(basis_name)



gamessparser=Parser()
with open(gamessparser.inputfile) as f:
    lines = f.readlines()
    for line in lines:
        gamessparser.extract(gamessparser, line)
