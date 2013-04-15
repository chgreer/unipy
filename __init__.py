#!/usr/bin/python
from struct import unpack

class sddfile:
    def __init__(self,fn):
        self.fn = fn
        self.index = []
        self.scans = []
        
        #read the file
        with open(self.fn, mode='rb') as file: # b is important -> binary
            self.content = file.read()
        self.filesize = len(self.content)
 
        #the bootstrap takes something like 32 bytes worth of 
        #useful info. don't know if this is universal.
        start = 0
        stop = 32

        #unpack the 8 ints for the bootstrap info
        res = unpack('iiiiiiii',self.content[start:stop])
        self.bootstrap = sddbootstrap(res,self.content)

        #end of bootstrap
        stop = self.bootstrap.bytes_per_rec
        
        #read in each index
        for i in range(self.bootstrap.num_used):
            start = stop
            stop = stop + self.bootstrap.bytes_per_index
            res = unpack('iiff16sffdffhhhh',self.content[start:stop])
            self.index.append(sddindex(res))

        #read in each scan
        #scan has preamble, header, then data
        for i in range(self.bootstrap.num_used):
            #compute where the scan preamble is and read it
            start = (self.index[i].start_rec-1)*self.bootstrap.bytes_per_rec
            stop =  start+32
            res = unpack('h'*16,self.content[start:stop])
            self.scans.append(sddscan(res))

            #the next double has the length of the overall header, which
            #comes after the preamble
            start = (self.index[i].start_rec-1)*self.bootstrap.bytes_per_rec
            nclass = len(self.scans[i].startword)
            for j in range(nclass):
                if self.scans[i].startword[j] == 0: 
                    #not all classes have to be included in a given file
                    #only thirteen are mandatory out of a possible 15
                    continue
                startbyte = start+8*(self.scans[i].startword[j]-1)
                stopbyte = startbyte+8*(self.scans[i].startword[j+1])
                if j == 12:
                    #this is a kludge to get the code to read the
                    #header info for the 13th class in sample ARO data
                    stopbyte = startbyte+8*7
 
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
        #different scan types are coded differently. this function
        #provides a lookup table so that the coded value can be
        #transferred to a human-readable one
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
        #constructor initializes the ssdscan object with information
        #from the SDD preamble
        self.numclass = tup[0]
        self.startword = []
        self.classes = []
        for i in range(1,16):
            self.startword.append(tup[i])

    def unpack_class(self,classnum,start,content):
        #each class header has a variety of different data in it
        #these strings are for the ARO SMT. Specifically some of the
        #later ones could be different for different telescopes.
        #format doc also suggests that the class headers could be
        #*longer* than specified in the document. This is not currently
        #handled.
        format_strings = ['ddd8s16s8s8s16s8s8s8s8sddd', \
            'dddddddddddd8s',\
            'dddddddd8sd',\
            'dddddddddddddddd8s',\
            'dddddd',\
            'dddddddddd8s',\
            'ddddd8s8s',\
            'ddddd',\
            'ddddddddddddddddddddddddd',\
            '8s8s8s8s8s8s8s8s8s8s',\
            'ddddddddddddddd16sddddddddddddddddddd',\
            'dddddddddddddddddddd8sd16s',\
            'ddddddd' ]

        startword = self.startword[classnum]
        stopword = self.startword[classnum+1]
        nwords = stopword-startword
        format_string = format_strings[classnum]
        word_codes = ''
        words_found=0

        #may not use all the available words in a header. include
        #as many as the preamble records tell you are used
        while words_found < nwords:
            jj=1 #number of steps in the format string
            new_code = format_string[len(word_codes):len(word_codes)+jj]

            #double strings are one character 'd'
            #character strings are either '8s','16s','24s', etc.
            while new_code[-1].isdigit() is True:
                jj += 1
                new_code=format_string[len(word_codes):len(word_codes)+jj]
            if new_code[0].isdigit():
                new_words_found = int(filter(str.isdigit,new_code))/8
            else:
                new_words_found = 1
            word_codes  += new_code
            words_found += new_words_found

        res = unpack(word_codes,content[start:start+8*(nwords)])
     
