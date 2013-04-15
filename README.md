uniPY
=======

Code to take Unipops (http://www.cv.nrao.edu/unipops/) SDD files and 
read them into python.

Example script:

#!/usr/bin/python
import unipy as upy

fn='uniPY/rogers_2012/sdd.gbc_002'

info = upy.sddfile(fn)
