# Comments about the system being studied 
&atoms nctype 3 natom 8
&atoms_types 3 natom 8
check &atoms_types  + {len(set(qcobj.atomnos))}   natom   {str(qcobj.natom)} + 
geometry
end
znuc
end
