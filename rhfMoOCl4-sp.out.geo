# Comments about the system being studied 
&atoms nctype 3 natom 6
&atoms_types 3 natom 6
check &atoms_types  + {len(set(qcobj.atomnos))}   natom   {str(qcobj.natom)} + 
geometry
end
znuc
end
