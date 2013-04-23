uniPY
=======

Code to take Unipops (http://www.cv.nrao.edu/unipops/) SDD files and 
read them into python.

The resulting sddfile object contains members:

1. A bootstrap object containing fundamental info about the sdd file.
	* sddfile.bootstrap
2. A list of index objects with numrec elements with crucial information about
each scan.
	* sddfile.index[numrec]
3. A list of scans, each with a header dict and numpy data array. The data
array can have multiple words of data for each scan. 
	* sddfile.scans[numrec].header{key} 
	* sddfile.scans[numrec].data[ndataword]

Example script:

    #!/usr/bin/python
    import unipy as upy

    fn='uniPY/rogers_2012/sdd.gbc_002'

    info = upy.sddfile(fn,'smt')
    ii = 2319

	print "Bootstrap:"
	print "Number of records:\t",info.bootstrap.numrec
	print "Number of data records:\t",info.bootstrap.numdata
	print "etc...."
	print ""
	print "Index:\t",ii
	print "start_rec\t",info.index[ii].start_rec
	print "stop_rec\t",info.index[ii].stop_rec
	print "etc...."
	print ""
	for jj in range(2318,info.bootstrap.num_used):
    	yr = int(info.scans[jj].header['utdate'])
    	hr = info.scans[jj].header['ut']
    	mn = (info.scans[jj].header['ut']-int(hr))*60
    	sc = (mn-int(mn))*60
    	src = info.scans[jj].header['object']
    	scan = info.scans[jj].header['scan']
    	scantyp = info.scans[jj].header['obsmode']
    	print '{0:4d} {1:6.2f} {2:02d} {3:02d} {4:04.1f} {5:8s} {6:8s}'\
			.format(jj,scan,int(hr),int(mn),sc,src,scantyp)
	
Example Script Output:

	Bootstrap:
	Number of records:	2049
	Number of data records:	11872
	etc....
	
	Index:	2319
	start_rec	13912
	stop_rec	13921
	etc....
	
	2318 3363.03 16 52 57.9 BLLAC            CONTVLBI
	2319 3363.04 16 52 57.9 BLLAC            CONTVLBI
