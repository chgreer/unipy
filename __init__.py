#!/usr/bin/python
from struct import unpack
import numpy as np

class sddfile:
    def __init__(self,fn,telescope):
        self.fn = fn
        self.telescope = telescope.lower()
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
        for ii in range(self.bootstrap.num_used):
            start = stop
            stop = stop + self.bootstrap.bytes_per_index
            res = unpack('iiff16sffdffhhhh',self.content[start:stop])
            self.index.append(sddindex(res))

        #read in each scan: has preamble, header, then data
        #preamble 32 bytes of data followed by zeros to length of one record
        #header and datalength are contained in the header
        for ii in range(self.bootstrap.num_used):
            start = (self.index[i].start_rec-1)*self.bootstrap.bytes_per_rec
            stop =  start+32
            res = unpack('h'*16,self.content[start:stop])
            self.scans.append(sddscan(res))
            self.scans[i].unpack_header(start,self.content)
            self.scans[i].unpack_data(start,self.content)
        
class sddbootstrap:
    """
    class containing the bootstrap info
    """
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
    """
    class containing the SDD file index info
    """
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
        """
        different scan types are coded differently. this function
        provides a lookup table so that the coded value can be
        transferred to a human-readable one
        """
        if self.mode < 512:
            obstype='cont'
            phs=256
        else:
            obstype='spec'
            phs=512
       
        code = self.mode - phs
        
        #this look-up table is on page 4 of the sdd file format pdf
        #assume it is valid for every telescope
        lut=['','PS','APS','FS','BSP','TPON','TPOF','ATP','PSM','APM',\
            'FSM','TPMO','TPMF','DRF','PCAL','BCAL','BLNK','SEQ',\
            'FIVE','MAP','FOC','NSFC','TTIP','STIP','DON','CAL','FSPS',\
            'BSPS','ZERO','TLPW','FQSW','NOCL','PLCL','ONOF','BMSW',\
            'PSSW','DRFT','OTF','SON','SOF','QK5','QK5A','PSS1','VLBI',\
            'PZC','CPZM','PSPZ','CPZ1','CPZ2']

        #some scans in test data have code not in lut, set to 0 
        #which means "No mode present". Possible bug.
        if code >= len(lut):
            retval = lut[0]
        else:
            retval = lut[code] 
        return retval
        
class sddscan:      
    def __init__(self,tup):
        """
        constructor initializes the ssdscan object with information
        from the SDD preamble
        """
        self.numclass = tup[0]
        self.startword = []
        self.header = {}
        self.data = np.array([])

        for i in range(1,16):
            self.startword.append(tup[i])

    def unpack_header(self,start,content):
        """
        each class header has a variety of different data in it
        these strings are for the ARO SMT. Specifically some of the
        later ones could be different for different telescopes.
        format doc also suggests that the class headers could be
        *longer* than specified in the document. This is not currently
        handled.
        """
        for classnum in range(self.numclass):
            if self.startword[classnum] == 0: 
                #not all classes have to be included in a given file
                #only thirteen are mandatory out of a possible 15
                continue
            startbyte = start+8*(self.startword[classnum]-1)
            stopbyte = startbyte+8*(self.startword[classnum+1])
            if classnum == 12:
                #this is a kludge to get the code to read the
                #header info for the 13th class in sample ARO data
                stopbyte = startbyte+8*7
            #self.scans[i].unpack_header(start,self.content)
        
            startword = self.startword[classnum]
            stopword = self.startword[classnum+1]
            nwords = stopword-startword
            format_string = self.get_format_string('smt',classnum)
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
                    #get the numbers from the new code and calc # of words
                    new_words_found = int(filter(str.isdigit,new_code))/8
                else:
                    new_words_found = 1
                word_codes  += new_code
                words_found += new_words_found

            res = unpack(word_codes,content[startbyte:startbyte+8*(nwords)])
            key_dict = self.get_key_dict('smt',classnum)
            for jj in range(len(res)):  
                self.header[key_dict[jj]] = res[jj]

    def unpack_data(self,start,content):
        """
        Data to read in the information about the scan from header and then
        read from content starting at the start byte to get the data into the
        sddscan object.
        """
        header = self.header
        hlen = int(header['headlen'])
        dlen = int(header['datalen'])
        ndataword = dlen/4
        startbyte = start+hlen
        stopbyte = startbyte+dlen
        res = unpack('f'*ndataword,content[startbyte:stopbyte])
        self.data = np.asarray(res)
        
    def get_format_string(self,telescope,classnum):
        """
        The header has a set format in the format doc. For a telescope
        string, will return the header format string to read in the data.
        Currently only 'smt' is supported for telescope.
        """
        if telescope=='smt':
            format_string =  \
                [ 'ddd8s16s8s8s16s8s8s8s8sddd', \
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
        else:
            print "NO RECOGNIZED FORMAT STRING FOR TELESCOPE ",telescope
            format_string = [];

        return format_string[classnum];

    def get_key_dict(self,telescope,classnum):
        if telescope=='smt':
            key_dict = { \
                0: ['headlen','datalen','scan','obsid','observer','telescop',\
                   'projid','object','obsmode','frontend','backend','precis'],\
                1: ['xpoint','ypoint','uxpnt','uypnt','ptcon0','ptcon1',\
                    'ptcon2','ptcon3','orient','focusr','focusv','focush',\
                    'pt_model'],\
                2: ['utdate','ut','lst','norchan','noswvar','nophase',\
                    'cycllen','samprat','cl11type'],\
                3: ['epoch','xsource','ysource','xref','yref','epocra',\
                    'epocdec','gallong','gallat','az','el','indx','indy',\
                    'desorg0','desorg1','desorg2','coordcd'],\
                4: ['tamb','pressure','humidity','refrac','dewpt','mmh2o'],\
                5: ['scanang','xzero','yzero','deltaxr','deltayr','nopts',\
                    'noxpts','noypts','xcell0','ycell0','frame'],\
                6: ['bfwhm','offscan','badchv','rvsys','velocity','veldef',\
                    'typecal'],\
                7: ['appeff','beameff','antgain','etal','etafss'],\
                8: ['synfreq','lofact','harmonic','loif','firstif','razoff',\
                    'reloff','bmthrow','bmorent','baseoff','obstol',\
                    'sideband','wl','gains','pbeam0','pbeam1','mbeam0',\
                    'mbeam1','sroff0','sroff1','sroff2','sroff3','foffsig',\
                    'foffref1','foffref2'],\
                9: ['openpar0','openpar1','openpar2','openpar3','openpar4',\
                    'openpar5','openpar6','openpar7','openpar8','openpar9'],\
                10: ['current_disk','bologain','sptip_start','sptip_stop',\
                    'ramp_up','tatms','taus','taui','tatmi','tchop','tcold',\
                    'gaini','count0','count1','count2','linename','refpt_vel',\
                    'tip_humid','tip_ref_flag','refract_45','ref_correct',\
                    'beam_num','burn_time','parallactic','az_offset',\
                    'el_offset','spares040','spares041','spares042',\
                    'spares050','spares051','spares052','spares053',\
                    'spares054','spares055'],\
                11: ['obsfreq','restfreq','freqres','bw','trx','tcal','stsys',\
                    'rtsys','tsource','trms','refpt','x0','deltax','inttime',\
                    'noint','spn','tauh20','th20','tauo2','to2','polariz',\
                    'effint','rx_info'],\
                12: ['nostac','fscan','lscan','lamp','lwid','ili','rms']
            }
        else:
            print "NO RECOGNIZED KEYDICT STRING FOR TELESCOPE ",telescope
            key_dict = {};

        return key_dict[classnum]

