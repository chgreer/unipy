#!/usr/bin/python
import sys
from struct import unpack

class sddfile:
    def __init__(self,fn):
        self.fn = fn
        self.sizeofint = 4
        with open(self.fn, mode='rb') as file: # b is important -> binary
            content = file.read()
        start = 0
        stop = 32
        self.size = len(content)
        res = unpack('iiiiiiii',content[start:stop])
        self.bootstrap = sddbootstrap(res,content)
        
        #for i in range(self.bootstrap.num_used):
        start = stop
        stop = stop + self.bootstrap.bytes_per_index
            
        res = unpack('iiff16sffdffhhhh',content[start:stop])
        
        self.idx = sddindex(res,content)
        
        #print res[1]
        #self.bootstrap.numrec = 17

class sddbootstrap:
    #class containing the bootstrap info
    def __init__(self,tup,content):
        self.numrec  = tup[0]
        self.numdata = tup[1]
        self.bytes_per_rec = tup[2]
        self.bytes_per_index = tup[3]
        self.num_used = tup[4]
        self.counter = tup[5]
        self.sddtyp = tup[6]
        self.sddver = tup[7]
        pad_size = (self.bytes_per_rec - 32)/4;
        self.pad = unpack("i" * pad_size,content[32:self.bytes_per_rec])

class sddindex:
    def __init__(self,tup,content):
        self.start_rec = tup[0]
        self.stop_rec = tup[1]
        self.hor = tup[2]
        self.vert = tup[3]
        self.src_name = tup[4]
        self.scannum = tup[5]
        self.fres = tup[6]
        self.restfreq = tup[7]
        self.lst = tup[8]
        self.utdate = tup[9]
        self.mode = tup[10]
        self.recnum = tup[11]
        self.poscode = tup[12]
        
        

#with open(fn, mode='rb') as file: # b is important -> binary
#    content = file.read()

#res = unpack('iiiiiiii',content[:32])

#print res
