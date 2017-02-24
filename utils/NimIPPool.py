#--*-- coding:utf-8 --*--
'''
Created on 2015��6��16��

@author: stm
'''
from utils import DebugLog
import os
import pickle



class IPRecords(object):
    '''
    Maintain the ip map list
    '''
    def __init__(self, ip, state):
        self.ip = ip
        self.state = state
        self.serial_num = ''
        
        
    def getip(self):
        return self.ip
    
    def getstate(self):
        return self.state
    
    def setState(self):
        self.state = 1
    
    def unsetState(self):
        self.state = 0
        
    def getSn(self):
        return self.serial_num
    
    def setSn(self, serialnum):
        self.serial_num = serialnum
    
    
class NimIPPool(object):
    '''
    classdocs
    '''
    availableip = []
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(NimIPPool, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
            
        return cls._instance
    
    
    def __init__(self):
        '''
        Constructor
        '''
        self.data_created = False
        self.data_empty = False
        
        self.file_name = "ippool.dat"
        records_dir_name = "records"
        if not os.path.exists(records_dir_name):
            os.mkdir(records_dir_name)
        self.file_name = os.path.join(records_dir_name, self.file_name)
        DebugLog.info_print("The ip pool file path: %s." % os.path.abspath(self.file_name))
        
        file_mode = "r+"
        if os.path.isfile(self.file_name):
            self.data_created = True
            file_mode = "r+"
        else:
            file_mode = "w+"
        
        self.file_handler = open(self.file_name, file_mode)
        if self.data_created:
            self.read_data(self.file_handler)
        else:
            self.init_data(self.file_handler)
        
        
    def __del__(self):
        '''
        Destructor
        '''
        self.file_handler.close()
        
        
    def init_data(self, filehdlr):
        self.ip_range = range(20, 200)
        for idx in self.ip_range:
            ip_prefix = "192.168.9."            
            NimIPPool.availableip.append(IPRecords(ip_prefix+str(idx),
                                         0)
                                    )
        self.cur_data_pointer = 0
        pickle.dump(NimIPPool.availableip, filehdlr)
        

    def read_data(self, filehdlr):
        NimIPPool.availableip = pickle.load(filehdlr)
    
        
    @staticmethod
    def getAvailableIP(serial_num):
        availip = None
        
        #length = len(self.availableip)
        #fcntl.flock(self.file_handler, fcntl.LOCK_EX)
        from utils.FileLock import FileLock

        with FileLock("myfile.lock"):
            # work with the file as it is now locked  
            temp_list = NimIPPool.availableip
            for tmpip in temp_list:
                if not tmpip.getstate() and not tmpip.getSn():
                    tmpip.setState()
                    tmpip.setSn(serial_num)
                    availip = tmpip.getip()
                    break
            #fcntl.flock(self.file_handler, fcntl.LOCK_UN)
        return availip 
    
            
    def releaseIP(self, ipstr):
        _ip_prefix, _ip_idx = ipstr.rsplit('.', 1)
        _idx = int(_ip_idx) - 20
        NimIPPool.availableip[_idx].unsetState()
        NimIPPool.availableip[_idx].setSn("")
            
        
        