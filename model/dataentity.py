#--*-- coding:utf-8 --*--
'''
Created on 2015��5��20��

@author: stm
'''
from model.viosmachine import VIOSMachineRecord, IP_ID, NAME_ID, SN_ID, PHASE,\
    DATA_COLS, PROGRESS, SEL_ID, IP_FOR_NIMINSTALL, IP_GW_FOR_NIMINSTALL
from utils import DebugLog
from base.msgcodec import MsgCodec
from base.cmdmsg import CMDMsg, SERVERSCAN, SAVESELECTION, GETSTATUS, \
    REMVSERVER, CREATEVIOSLPAR, CHECKCREATEVIOSLPAR, UPDATESTATUS
import time
import pickle
import os.path
import string
from base.vdstate import PRGRS_FINISHED, StateBase
from utils.PingTest import PingTest
from utils.NimIPPool import NimIPPool

class DataEntity(object):
    '''
    classdocs
    '''
    
    
    def __init__(self, vd_config):
        '''
        Constructor
        '''
        self.config = vd_config
        self.machine_records = []
        self.ip_pool_obj = NimIPPool()
        
        self.msg_decoder = MsgCodec()
        self.data_created = False
        self.data_empty = False

        self.file_name = "data_"+time.strftime("%Y_%m_%d_%H_%M_%S.dat", time.gmtime())
        records_dir_name = "records"
        if not os.path.exists(records_dir_name):
            os.mkdir(records_dir_name)
        self.file_name = os.path.join(records_dir_name, self.file_name)
        DebugLog.info_print("The record file path: %s." % os.path.abspath(self.file_name))
        self.file_handler = open(self.file_name, "wb")
        self.init_data()
        self.cur_data_pointer = 0


    def __del__(self):
        '''
        Destructor
        '''
        self.file_handler.close()
        

    def init_data(self):       
        for idx in range(10):
            self.machine_records.append(VIOSMachineRecord())
            self.machine_records[idx].setIndex(idx)
        
        ip_nim_internal = self.config.get('nimserver_ip_pool', 'ip_pool_startip')
        self.ip_nim_internal_prefix, self.ip_nim_internal_base = \
                          string.rsplit(ip_nim_internal, '.', 1)
                          
        self.ip_gw_nim_internal = self.config.get('nimserver_ip_pool', 
                                                  'ip_pool_gateway_ip')
        pickle.dump(self.machine_records, self.file_handler)
        
            
    def test_existed(self, sn_tested):
        sn_existed_list = []
        bexisting = False
        
        if 0 == self.cur_data_pointer:
            bexisting = False  
        else:
            for indx in range(self.cur_data_pointer):
                sn_existed_list.append(self.machine_records[indx].getSerialNm())
            bexisting = sn_tested in sn_existed_list 
        return bexisting
    
    
    
    def savedata(self, msg_body):
        '''
        Data format: name, ip_addr, sn, state
        '''
        DebugLog.debug_print_level1(msg_body)
        _cmd_key, _server_id, data = self.msg_decoder.decodeMsg(msg_body)
        
        #data_list = eval(data)
        data_list = self.reformat(data)
        #_ret_cmd, msg_body = 
        # name, ip_addr, serial_nm, stat
        isempty = len(data_list[0]) < 2
        if CMDMsg.getCMD(SERVERSCAN) == _cmd_key:
            if isempty:
                return
            
            if not self.data_created:
                self.data_created = True
            
                
            MSG_IDS_MAP = [NAME_ID, IP_ID, SN_ID, PHASE] 
            for idx in range(len(data_list)):
                # 2: SN_ID, 3: PHASE, 
                phase_info = data_list[idx][3]
                if phase_info.endswith("No Connection"):
                    DebugLog.info_print("Got server %s status: %s" % 
                                        (data_list[idx][0], phase_info))
                    continue
                
                sn_tested = data_list[idx][2]
                if self.test_existed(sn_tested):
                    continue
                
                pointer_indx = self.cur_data_pointer
                for n_id in range(len(MSG_IDS_MAP)):
                    self.machine_records[pointer_indx].updateValue(
                                                      MSG_IDS_MAP[n_id],
                                                      data_list[idx][n_id])

                self.machine_records[pointer_indx].updateValue(
                                                PROGRESS,
                                                StateBase.get_state_progress_const_name(PRGRS_FINISHED))

                
#                 ip_nim_internal_temp = "%s.%s" % \
#                                   (self.ip_nim_internal_prefix, 
#                                    int(self.ip_nim_internal_base) + pointer_indx*10)
#                 ip_test_obj = PingTest(ip_nim_internal_temp, 10)
                
                #_ip_nim_internal = self.ip_pool_obj.getAvailableIP(sn_tested)
                #ip_pool_obj = NimIPPool()
                _ip_nim_internal = NimIPPool.getAvailableIP(sn_tested)
                
                self.machine_records[pointer_indx].updateValue(IP_FOR_NIMINSTALL,
                                                               _ip_nim_internal)
                self.machine_records[pointer_indx].updateValue(IP_GW_FOR_NIMINSTALL,
                                                               self.ip_gw_nim_internal)
                self.cur_data_pointer += 1
                                                      
        elif CMDMsg.getCMD(SAVESELECTION) == _cmd_key:
            data_row_id = int(_server_id) 
            data_val = bool(int(data_list[0][0]))
            self.machine_records[data_row_id].updateValue(SEL_ID, data_val)
            
#         elif CMDMsg.getCMD(REMVSERVER) == _cmd_key:
#             data_row_id = int(_server_id)
#             data_val = '[Removed from HMC]'
#             self.machine_records[data_row_id].updateValue(PHASE, data_val)
            
        elif CMDMsg.getCMD(CREATEVIOSLPAR) == _cmd_key or \
             CMDMsg.getCMD(CHECKCREATEVIOSLPAR) == _cmd_key:
            data_row_id = int(_server_id)
            _phase, _progress = eval(data)
            self.machine_records[data_row_id].updateValue(PHASE, _phase)
            self.machine_records[data_row_id].updateValue(PROGRESS, _progress)
            
                    
        elif CMDMsg.getCMD(GETSTATUS) == _cmd_key:
            DebugLog.debug_print_level1("In data entity: save data,  " + str(msg_body))
            if self.data_created:
                # update server state or name only if the sn is equal
                ret_id_name  = 0
                ret_id_sn    = 2
                ret_id_state = 3

                for idx in range(len(data_list)):
                    for server_idx in range(len(self.machine_records)):
                        if data_list[idx][ret_id_sn] == self.machine_records[server_idx].getSerialNm():
                            if self.machine_records[server_idx].get_stage_id_val() < CREATEVIOSLPAR:
                                if not (self.machine_records[server_idx].getState() == data_list[idx][ret_id_state]):
                                    self.machine_records[server_idx].setState(data_list[idx][ret_id_state])
                                if not (self.machine_records[server_idx].getServerName() == data_list[idx][ret_id_name]):
                                    self.machine_records[server_idx].setServerName(data_list[idx][ret_id_name])                

            pickle.dump(self.machine_records, self.file_handler)
            
        elif CMDMsg.getCMD(UPDATESTATUS) == _cmd_key:
            data_row_id = int(_server_id)
            
            _phase, _progress, _server_name = eval(data)
            self.machine_records[data_row_id].updateValue(PHASE, _phase)
            self.machine_records[data_row_id].updateValue(PROGRESS, _progress)
            self.machine_records[data_row_id].updateValue(NAME_ID, _server_name)
        else:
            data_row_id = int(_server_id)
            _phase, _progress = eval(data)
            self.machine_records[data_row_id].updateValue(PHASE, _phase)
            self.machine_records[data_row_id].updateValue(PROGRESS, _progress)

        
    def reformat(self, body):
        data_list = None
        if isinstance(body, str):
            data_list = body[2:-2].split("', '")
        elif isinstance(body, list):
            data_list = body
            
        format_data_list = []
        totalcol = 4
        row = len(data_list)
        for row_indx in range(row):
            temp = data_list[row_indx].split(",")
#             for indx in range(totalcol):
#                 temp.append(data_list[row_indx * totalcol + indx])
            format_data_list.append(temp)
    
        return format_data_list
    
    
    def updateAndSaveDataByName(self, body):
        '''
        Data format: name, state
        '''
        data_list = self.reformat(body)
        
        # name, ip_addr, serial_nm, stat
        for idx in range(len(data_list)):
            for machine_record_id in range(DATA_COLS):
                if self.machine_records[machine_record_id].getServerName() == data_list[idx][0]:
                    self.machine_records[machine_record_id].setState(data_list[idx][1])
                    
        
    def retrieve(self):
        '''
        return the data as:
        [ [AUTO_FLAG, SEL_ID, IDX_ID, IP_ID, PORT_ID, SN_ID, PHASE, PROGRESS, NAME_ID, IP_FOR_NIMINSTALL, IP_GW_FOR_NIMINSTALL],
          [SEL_ID, IDX_ID, IP_ID, PORT_ID, SN_ID, PHASE, PROGRESS, NAME_ID],
          [SEL_ID, IDX_ID, IP_ID, PORT_ID, SN_ID, PHASE, PROGRESS, NAME_ID],
        ]
        
        '''
        data_ret = []
        
        if not self.machine_records:
            data_ret = None
            
        for row_idx in range(len(self.machine_records)):
            data_temp = []
            for col_idx in range(DATA_COLS):
                data_temp.append(self.machine_records[row_idx].getValueById(col_idx))
            data_ret.append(data_temp)
            
        return data_ret
    
    def get_data_status_key(self, idx):
        '''
        get data status by id
        The format is "PROGRESS"+"_"+"PHASE"
        '''
        assert(idx < len(self.machine_records))
        server_data = self.getServerData(idx)
        progress = server_data[PROGRESS]
        phase_name = server_data[PHASE]
        #return stage_name + '_' + state_name
        return (phase_name, progress)
        
        
    def update_data_status(self, idx, status):
        self.machine_records[idx].updateValue(PROGRESS, status)
    
    def getCheckedItemsList(self):
        
        data_lst = self.retrieve()
        data_ret = []
        for idx in range(len(data_lst)):
            if data_lst[idx][SEL_ID]:
                data_ret.append(data_lst[idx][:])
                
        return data_ret
            
    
    def getServerData(self, server_id):
        data_lst = self.retrieve()
        return data_lst[server_id]
    
    
    def getServerCount(self):
        return len(self.machine_records)
        
