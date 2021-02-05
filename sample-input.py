import pychamp
import numpy as np
import sys




for filename in [ "piece.txt"]:

    data = pychamp.io.qcread(filename)

#    print(dir(data))
#    print(f"There are {data.natom} atoms and {data.nbasis} number of cartesian basis")
#    print(f"There are charges {data.charge} ")

#    for element in range(len(data.atomnos)):
#        print(data.atomnos[element], data.atomcoords[0][element])



    # print(f"The MO coefficients {data.mocoeffs[0][0]}")

    # print(f"The MO energies {data.moenergies}")

    # print(f"The MO symmetries {data.mosyms}")

    # values, counts = numpy.unique(data.mosyms, return_counts=True)

    # print (len(counts))

    # print(f"unique irreducible representations {dict(zip(values,counts))}")        

    # print(f"The basis set {data.gbasis[0]}")

    # print(f"The SCF energies {data.scfenergies}")

    # print(f"The metadata {data.metadata}")


#    pychamp.io.qcwrite(data, outputtype="xyz", outputdest="output.xyz")
    
    

    pychamp.io.write_champ_old_sym(data, outputdest="rhf" + filename)


    # print("sym_labels", len(counts), len(data.mosyms[0]))

    # # irreducible representations of various groups
    # c2v = { "A1":1, "B1":2, "B2":3, "A2":4 }  

    # if all(irreps in data.mosyms[0] for irreps in ["A1", "B1", "B2", "A2"]):
    #     print ("1 A1 4 A2 2 B1 3 B2")
    #     for item in data.mosyms[0]:
    #         for key, val in c2v.items():
    #             if item == key:
    #                 print (val)
    #     print ()
    # print("end")                
    # with open("test.geo", 'w') as file:
        
    #     # header line printed below                
    #     file.write("# Comments about the system being studied \n")
    #     file.write("&atoms nctype " + str(len(set(data.atomnos))) + " natom " + str(data.natom) + "\n" )
        

    #     # Get the list of unique elements of the list and the index of them (note python indenxing starts at 0)
    #     unique_elements, indices = np.unique(data.atomnos, return_inverse=True)

    #     element_string = ""
    #     for i, val in enumerate(unique_elements):
    #         element_string += " " + str(i+1) + " " + str(pt.elements[val].symbol)        
    #     file.write("&atoms_types " + element_string + "\n" )                
    #     file.write("geometry\n")                

    #     coords = [[data.atomcoords[0][i][j] for j in range(3)] for i in range(len(data.atomnos))]
    #     coords = np.array(coords)/0.5291772109 #angstrom_to_bohr conversion

    #     for element in range(len(data.atomnos)):
    #         file.write("{: 0.6f} {: 0.6f} {: 0.6f} {} \n".format(coords[element][0], coords[element][1], coords[element][2], indices[element]+1)) 

    #     file.write("end\n")                
    #     file.write("znuc\n")                                
    #     core  = Core()
    #     for element in np.unique(data.atomnos):
    #         file.write("{: 0.6f} ".format(core.valence[element]) ) 

    #     file.write("\n")                
    #     file.write("end\n")                
    # file.close()
