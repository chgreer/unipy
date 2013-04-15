#!/usr/bin/python
import sys
from struct import unpack

class sddfile:
    def __init__(self,fn):
        self.fn = fn
        self.sizeofint = 4
        self.index = []
        self.scans = []
        
        #read the file
        with open(self.fn, mode='rb') as file: # b is important -> binary
            self.content = file.read()
        self.filesize = len(self.content)
 
        #the bootstrap takes something like 32 bytes worth of 
        #useful info
        start = 0
        stop = 32

        #unpack the 8 ints for the bootstrap info
        res = unpack('iiiiiiii',self.content[start:stop])
        self.bootstrap = sddbootstrap(res,self.content)

        #end of bootstrap
        stop = self.bootstrap.bytes_per_rec
        
        #read in index for each scan
        for i in range(self.bootstrap.num_used):
            start = stop
            stop = stop + self.bootstrap.bytes_per_index
            res = unpack('iiff16sffdffhhhh',self.content[start:stop])
            self.index.append(sddindex(res))

        #read in each scan
        for i in range(self.bootstrap.num_used):
            #compute where the scan preamble is and read it
            start = (self.index[i].start_rec-1)*self.bootstrap.bytes_per_rec
            stop =  start+32
            res = unpack('h'*16,self.content[start:stop])
            self.scans.append(sddscan(res))
            #print res

            #the next double has the length of the overall header, which
            #comes after the preamble
            start = (self.index[i].start_rec-1)*self.bootstrap.bytes_per_rec
            #skip the preamble
            nclass = len(self.scans[i].startword)
            for j in range(nclass):
                if self.scans[i].startword[j] == 0: 
                    continue
                startbyte = start+8*(self.scans[i].startword[j]-1)
                stopbyte = startbyte+8*(self.scans[i].startword[j+1])
                if j == 12:
                    stopbyte = startbyte+8*7
                nwords = (stopbyte-startbyte)/8
                self.scans[i].unpack_class(j,startbyte,self.content)
        
        
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
    #class containing the SDD file index info
    def __init__(self,tup):
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
        self.posshrt = self.decode_poscode()
        self.pad = tup[13]

    def decode_poscode(self):
        if self.mode < 512:
            obstype='cont'
            phs=256
        else:
            obstype='spec'
            phs=512
       
        code = self.mode - phs
        lut=['','PS','APS','FS','BSP','TPON','TPOF','ATP','PSM','APM',\
            'FSM','TPMO','TPMF','DRF','PCAL','BCAL','BLNK','SEQ',\
            'FIVE','MAP','FOC','NSFC','TTIP','STIP','DON','CAL','FSPS',\
            'BSPS','ZERO','TLPW','FQSW','NOCL','PLCL','ONOF','BMSW',\
            'PSSW','DRFT','OTF','SON','SOF','QK5','QK5A','PSS1','VLBI',\
            'PZC','CPZM','PSPZ','CPZ1','CPZ2']
        if code >= len(lut):
            retval = lut[0]
        else:
            retval = lut[code] 
        return retval
        
class sddscan:      
    def __init__(self,tup):
        self.numclass = tup[0]
        self.startword = []
        self.classes = []
        for i in range(1,16):
            self.startword.append(tup[i])

    def unpack_class(self,classnum,start,content):
        format_strings = ['ddd8s16s8s8s16s8s8s8s8sddd', \
            'dddddddddddd8s','dddddddd8sd','dddddddddddddddd8s',\
            'dddddd','dddddddddd8s','ddddd8s8s','ddddd',\
            'ddddddddddddddddddddddddd',\
            '8s8s8s8s8s8s8s8s8s8s',\
            'ddddddddddddddd16sddddddddddddddddddd',\
            'dddddddddddddddddddd8sd16s','ddddddd' ]
        #print "unpacking class " + str(classnum)
        startword = self.startword[classnum]
        stopword = self.startword[classnum+1]
        nwords = stopword-startword
        format_string = format_strings[classnum]
        word_codes = ''
        words_found=0
        while words_found < nwords:
            jj=1
            word_codes = format_string[0:len(word_codes)+1]
            while word_codes[-1].isdigit() is True:
                word_codes = format_string[0:(len(word_codes)+1)]
                jj+=1
            if jj > 2:
                words_found+=(jj-2)
            words_found+=1
        res = unpack(word_codes,content[start:start+8*(nwords)])
     
