#--*-- coding:utf-8 --*--
'''
Created on 2015��5��20��

@author: stm
'''
from utils import DebugLog
from base.cmdmsg import CMDMsg, SERVERSCAN, UPDATEPASSWD, CHECKUPDATEPASSWD, REMVSERVER, CHECKREMVSERVER,\
    POWEROFFSERVER, CHECKPOWEROFFSERVER, GETSTATUS, CHECKRECOVERPROFILE, \
    RST_FW_FCTRY, CHECKRST_FW_FCTRY, RECOVERPROFILE, POWERONSERVER, CHECKPOWERONSERVER, \
    SAVESELECTION, RMV_NON_HMC, CHECKRMV_NON_HMC, CREATEVIOSLPAR,\
    PREPAREHOSTSFILE, DEFINESERVER, CHECKDEFINEDSERVER, ASSIGNRESOURCE, INSTALLVIOS,\
    CHECKCREATEVIOSLPAR, CHECKHOSTSFILE, CHECKASSIGNEDRESOURCE, CHECKVIOSINSTALL,\
    ACCEPTLICENSE, CHECKACCEPTLICENSE, UPDATESTATUS, CLEANNIMRESOURCE,\
    CHECKCLEANSTATUS, ASM_POWERON, CHECKASM_POWERON, INSTALLSW, SET_DEFAULT_IP, \
    AUTOSTART, INSTALL_VIOS_ONLY, SET_DEFAULT_IP_AND_SHUTDOWN
    
from base.msgcodec import MsgCodec
    
from engine.helloeng import HelloEng
from engine.hmceng import HMCEng
from engine.asmieng import AsmiEng
from model.viosmachine import IDX_ID, NAME_ID, IP_ID, SN_ID, IP_FOR_NIMINSTALL, PROGRESS,\
    PHASE
from engine.nimeng import NIMEng
from base.CoreTask import CoreTask
from base.vdstate import VD_READY, SERVERSCAN_STAT, PASSWORD_REQUIRED_STAT, \
                         FAILED_AUTH_STAT, ASM_POWERON_STAT, \
                         UPDATEPASSWD_STAT, RECOVERY_STAT, RECOVERPROFILE_STAT, \
                         POWEROFF_STAT, POWERONSERVER_STAT, OPERATING_STAT, \
                         STANDBY_STAT, CREATEVIOSLPAR_STAT, \
                         PREPAREHOSTSFILE_STAT, DEFINESERVER_STAT, ASSIGNRESOURCE_STAT, \
                         INSTALL_VIOS_STAT, POWEROFFSERVER_STAT, REMVSERVER_STAT, \
                         RST_FW_FCTRY_STAT, RMV_NON_HMC_STAT, VD_END,\
    StateBase, PRGRS_READY, PRGRS_INPROGRESS, ACCEPTLICENSE_STAT,\
    CLEAN_NIM_RESOURCE_STAT, PRGRS_FINISHED, INSTALLSW_STAT, SET_DEFAULT_IP_STAT,\
    SET_DEFAULT_IP_AND_SHUTDOWN_STAT
from utils.ErrorHandler import ActionIsNotExpected_Exception
import tkMessageBox
from threading import Thread
from engine.ServerEng import ServerEng


class SvrController(object):
    '''
    The server controller would handle the command from UI which includes sendMsg and retrvMsg
    and the data would be saved into server entities and fetched from the only data source.
    Then the controller also deals with the communication center
    '''  
    
    def __init__(self, config, communicate_center, dataentity):
        '''
        Constructor
        '''
        self.communicate_center = communicate_center
        self.dataentity = dataentity
        self.fsm_manager= []
        self.msg_coder = MsgCodec()
        self.config = config
        self.init_dataentity_fsm_manager()
        self.start_eng()
        self.auto_install = False
        self.b_server_removed_frm_hmc_flg = False
        
    
    def get_lpar_current_status(self, server_id):
        DebugLog.debug_print_level1("in server controller get_lpar_current_status")
        server_data = self.getServerData(server_id)
        
        params = [server_data[NAME_ID], server_data[SN_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(CHECKCREATEVIOSLPAR), server_data[IDX_ID], params)  #"UPDATE_PASSWD"
        self._sendMsg2CommCnt(msg)

    
    
    def get_nimserver_hosts_current_status(self, server_id):
        DebugLog.debug_print_level1("in server controller get_lpar_current_status")
        server_data = self.getServerData(server_id)
        
        params = [server_data[IP_FOR_NIMINSTALL], server_data[SN_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(CHECKHOSTSFILE), server_data[IDX_ID], params)  #"UPDATE_PASSWD"
        self._sendMsg2CommCnt(msg)
    
    
    def get_nimserver_defined_resource_current_status(self, server_id):
        DebugLog.debug_print_level1("in server controller get_nimserver_defined_resource_current_status")
        server_data = self.getServerData(server_id)
        
        params = [server_data[SN_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(CHECKDEFINEDSERVER), server_data[IDX_ID], params)  #"UPDATE_PASSWD"
        self._sendMsg2CommCnt(msg)
        

    def get_nimserver_assigned_resource_status(self, server_id):
        DebugLog.debug_print_level1("in server controller get_nimserver_assigned_resource_status")
        server_data = self.getServerData(server_id)
        
        params = [server_data[SN_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(CHECKASSIGNEDRESOURCE), server_data[IDX_ID], params)  #"UPDATE_PASSWD"
        self._sendMsg2CommCnt(msg)
            
    
    def get_vios_installation_status(self, server_id):
        DebugLog.debug_print_level1("in server controller get_vios_installation_status")
        server_data = self.getServerData(server_id)
        
        params = [server_data[IP_FOR_NIMINSTALL]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(CHECKVIOSINSTALL), server_data[IDX_ID], params)  #"UPDATE_PASSWD"
        self._sendMsg2CommCnt(msg)
        
        
    def get_asm_poweron_status(self, server_id):
        DebugLog.debug_print_level1("in server controller get_vios_installation_status")
        server_data = self.getServerData(server_id)
        
        params = [server_data[IP_FOR_NIMINSTALL]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(CHECKASM_POWERON), server_data[IDX_ID], params)  #"UPDATE_PASSWD"
        self._sendMsg2CommCnt(msg)

    
    
    def get_asmi_server_current_status(self):
        pass
    
    
    def get_recoverprofile_status(self, server_id):
        '''
        check recover profile status
        ''' 
        DebugLog.debug_print_level1("in server controller get_update_password_status")
        server_data = self.getServerData(server_id)
        params = [server_data[NAME_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(CHECKRECOVERPROFILE), server_data[IDX_ID], params)  #"GET_STATUS"
        self._sendMsg2CommCnt(msg)
    
    
    def accept_license_and_enable_root_user(self, server_id):
        '''
        send accept license and enable root user message to communication center
        '''
        DebugLog.debug_print_level1("in server controller accept_license_and_enable_root_user")
        server_data = self.getServerData(server_id)
        
        params = [server_data[IP_FOR_NIMINSTALL]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(ACCEPTLICENSE), server_data[IDX_ID], params)
        self._sendMsg2CommCnt(msg)
    
    
    def check_accept_license_and_enable_root_user(self, server_id):
        '''
        Check if accept license action done
        '''
        DebugLog.debug_print_level1("in server controller check_accept_license_and_enable_root_user")
        server_data = self.getServerData(server_id)
        
        params = [server_data[IP_FOR_NIMINSTALL]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(CHECKACCEPTLICENSE), server_data[IDX_ID], params)
        self._sendMsg2CommCnt(msg)
    
    
    def check_poweroff_process(self, server_id):
        '''
        Check if server is power off status
        '''
        DebugLog.debug_print_level1("in server controller check_poweroff_process")
        server_data = self.getServerData(server_id)
        
        params = [server_data[NAME_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(CHECKPOWEROFFSERVER), server_data[IDX_ID], params)
        self._sendMsg2CommCnt(msg)
    
    
    def init_dataentity_fsm_manager(self):
        '''
        initialize the fsm manager with the controller methods
        '''
        
        for count in range(self.dataentity.getServerCount()):
            self.fsm_manager.append(CoreTask(count))
            fsm_manager = self.fsm_manager[count]

            for state_idx in range(fsm_manager.get_state_count()):
                _act_func = None
                _check_handler = None
                if VD_READY == state_idx:
                    _act_func = self.server_scan
                elif SERVERSCAN_STAT == state_idx:
                    _act_func = self.update_server_password
                    _check_handler = self.get_server_current_status
                elif PASSWORD_REQUIRED_STAT == state_idx:
                    _act_func = self.update_server_password
                    _check_handler = self.get_update_password_status
                elif FAILED_AUTH_STAT == state_idx:
                    _act_func = self.update_server_password
                    _check_handler = self.get_update_password_status
                elif UPDATEPASSWD_STAT == state_idx:
                    _act_func = self.update_server_password
                    _check_handler = self.get_update_password_status
#                 elif RECOVERY_STAT == state_idx:
#                     _act_func = self.hmc_recover_server
#                     _check_handler = self.get_server_current_status
                elif RECOVERPROFILE_STAT == state_idx:
                    _act_func = self.hmc_recover_server
                    _check_handler = self.get_recoverprofile_status
#                 elif OPERATING_STAT == state_idx:
#                     _act_func = self.create_vios_lpar
#                     _check_handler = self.get_server_current_status
#                 elif STANDBY_STAT == state_idx:
#                     _act_func = self.create_vios_lpar
#                     _check_handler = self.get_lpar_current_status
                elif CREATEVIOSLPAR_STAT == state_idx:
                    _act_func = self.create_vios_lpar
                    _check_handler = self.get_lpar_current_status
                    
                elif PREPAREHOSTSFILE_STAT == state_idx:
                    _act_func = self.nimserver_prepare_host_file
                    _check_handler = None #self.get_nimserver_hosts_current_status
                elif DEFINESERVER_STAT == state_idx:
                    _act_func = self.nimserver_define_nim_host
                    _check_handler = self.get_nimserver_defined_resource_current_status
                elif ASSIGNRESOURCE_STAT == state_idx:
                    _act_func = self.nim_allocat_resource
                    _check_handler = self.get_nimserver_assigned_resource_status
                elif INSTALL_VIOS_STAT == state_idx:
                    _act_func = self.install_vios_server
                    _check_handler = self.get_vios_installation_status
                elif ACCEPTLICENSE_STAT == state_idx:
                    _act_func = self.accept_license_and_enable_root_user
                    _check_handler = self.check_accept_license_and_enable_root_user   
                elif CLEAN_NIM_RESOURCE_STAT == state_idx:
                    _act_func = self.clean_nim_resource
                    _check_handler = self.check_nim_resource_clean
                elif SET_DEFAULT_IP_STAT == state_idx:
                    _act_func = self.set_default_ip
                    _check_handler = None               
                elif POWEROFFSERVER_STAT == state_idx:
                    _act_func = self.poweroffserver
                    _check_handler = self.check_poweroff_process #self.get_server_current_status
                elif POWERONSERVER_STAT == state_idx:
                    _act_func = self.poweronserver
                    _check_handler = self.get_server_poweron_status
                elif REMVSERVER_STAT == state_idx:
                    _act_func = self.remove_server_from_hmc
                    _check_handler = None #self.get_asmi_server_current_status
                elif RST_FW_FCTRY_STAT == state_idx:
                    _act_func = self.hmc2ivm_rst_fw_factory_settings
                    _check_handler = None #self.get_asmi_server_current_status
                elif RMV_NON_HMC_STAT == state_idx:
                    _act_func = self.remove_nonhmc_connection
                    _check_handler = None #self.get_asmi_server_current_status
                elif ASM_POWERON_STAT == state_idx:
                    _act_func = self.asm_poweron
                    _check_handler = self.get_asm_poweron_status
                elif INSTALLSW_STAT == state_idx:
                    _act_func = self.installsw
                    _check_handler = None 
                elif SET_DEFAULT_IP_AND_SHUTDOWN_STAT == state_idx:
                    _act_func = self.set_default_ip_and_shutdown
                    _check_handler = None  
                else:
                    pass                                                
                    
                fsm_manager.set_states_acts(state_idx, _act_func)
                fsm_manager.set_status_check_handler(state_idx, _check_handler)
                

    
    def _sendMsg2CommCnt(self, msg, delayed=False):
        if not delayed:
            self.communicate_center.sendMessage(msg)
        else:
            self.communicate_center.sendDelayedMessage(msg)
    
    
    def check_server_in_fsm_manager(self):
        for server_manager_indx in range(len(self.fsm_manager)):
            phase, state = self.dataentity.get_data_status_key(server_manager_indx)
            fsm_manager = self.fsm_manager[server_manager_indx]
            DebugLog.debug_print_level1('state name : %s' % state)
            #if not fsm_manager.inprogress:
            fsm_manager.setTaskState(phase, state, first=True)
            
    def start_server_in_fsm_manager(self, server_id, phase=None, progress=None):
        if phase and progress:
            phase = phase
            state = progress
        else:
            phase, state = self.dataentity.get_data_status_key(server_id)
        fsm_manager = self.fsm_manager[server_id]
        if progress:
            state = progress 
        DebugLog.debug_print_level1('state name : %s' % state)
            #if not fsm_manager.inprogress:
        fsm_manager.setTaskState(phase, state)
    
    
    def setServerTaskState(self, _cmd_key, _server_id, data):
        if CMDMsg.getCMD(SAVESELECTION) == _cmd_key:
            pass
        elif CMDMsg.getCMD(SERVERSCAN) == _cmd_key:
            DebugLog.info_print("in setServerTaskState function: SERVERSCAN branch")
            self.check_server_in_fsm_manager()
        else:
            fsm_manager = self.fsm_manager[int(_server_id)]
            _data = eval(data)      
            phase = _data[0]
            state = _data[1]
            fsm_manager.setTaskState(phase, state)
    
    
    def updateData(self, msg):
        DebugLog.debug_print_level1("in updateData function in controller")
        self.dataentity.savedata(msg)
        _cmd_key, _server_id, data = self.msg_coder.decodeMsg(msg)
        if CMDMsg.getCMD(UPDATEPASSWD) == _cmd_key:
            self.b_server_removed_frm_hmc_flg = True
        self.setServerTaskState(_cmd_key, _server_id, data)


    def retrieve(self):
        DebugLog.debug_print_level1("Retrieve server data from dataentity")
        data_retrv = self.dataentity.retrieve()
        for data_indx in range(len(data_retrv)):
            fsm_manager = self.fsm_manager[data_indx]
            data_itm = data_retrv[data_indx]
            data_itm[PHASE] = fsm_manager.getTaskPhase()
            data_itm[PROGRESS] = fsm_manager.getTaskStateProgress()
        
        return data_retrv
    
    
    def retrieveMsg(self, msg):
        #self.dataentity
        pass #return self.dataentity.re
        
    def server_scan(self):
        
        if self.b_server_removed_frm_hmc_flg:
            return
        
        DebugLog.debug_print_level1("in server controller server_scan")

        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(SERVERSCAN), "_")
        self._sendMsg2CommCnt(msg)
        

    def get_server_current_status(self, server_id):
        '''get current status'''
        DebugLog.debug_print_level1("in server controller get_server_current_status")

        server_data = self.getServerData(server_id)
        params = [server_data[NAME_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(GETSTATUS), server_data[IDX_ID], params)  #"GET_STATUS"
        self._sendMsg2CommCnt(msg)


    def get_server_poweron_status(self, server_id):
        '''get current status'''
        DebugLog.debug_print_level1("in server controller get_server_poweron_status")

        server_data = self.getServerData(server_id)
        params = [server_data[NAME_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(CHECKPOWERONSERVER), server_data[IDX_ID], params)  #"GET_STATUS"
        self._sendMsg2CommCnt(msg)
        
    
    def get_update_password_status(self, server_id):
        '''
        check update password status
        ''' 
        DebugLog.debug_print_level1("in server controller get_update_password_status")
        server_data = self.getServerData(server_id)
        params = [server_data[SN_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(CHECKUPDATEPASSWD), server_data[IDX_ID], params)  #"GET_STATUS"
        self._sendMsg2CommCnt(msg)
        
                       
    def get_all_server_current_status(self):
        '''get current status'''
        DebugLog.debug_print_level1("in server controller get_server_current_status")
#         ckecked_items_id_list = self.getCheckedItemsIdList()
#         for item_id in range(len(ckecked_items_id_list)):
#             server_data = ckecked_items_id_list[item_id]
#             params = [server_data[NAME_ID]]
#             msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(GETSTATUS), server_data[IDX_ID], params)  #"GET_STATUS"
#             self._sendMsg2CommCnt(msg)
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(GETSTATUS), "_", None)
        self._sendMsg2CommCnt(msg)

        
        
    def getCheckedItemsIdList(self):
        return self.dataentity.getCheckedItemsList()
    
    
    def getServerData(self, server_id):
        return self.dataentity.getServerData(server_id)
    
    
    def update_server_password(self, server_id):
        '''
        [SEL_ID, IDX_ID, IP_ID, PORT_ID, SN_ID, STATE_ID, DEPLOY_PROGRESS, NAME_ID]
        '''
        DebugLog.debug_print_level1("in server controller update_server_password")
        server_data = self.getServerData(server_id)
        
        params = [server_data[NAME_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(UPDATEPASSWD), server_data[IDX_ID], params)  #"UPDATE_PASSWD"
        self._sendMsg2CommCnt(msg)
        

    def hmc_recover_server(self, server_id):
        '''
        [SEL_ID, IDX_ID, IP_ID, PORT_ID, SN_ID, STATE_ID, DEPLOY_PROGRESS, NAME_ID]
        '''
        DebugLog.debug_print_level1("in server controller update_server_password")
        server_data = self.getServerData(server_id)
        
        params = [server_data[NAME_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(RECOVERPROFILE), server_data[IDX_ID], params)  #"UPDATE_PASSWD"
        self._sendMsg2CommCnt(msg)
        
        #self.get_server_current_status() 
        
        
    def hmc_poweron_server(self, server_id):
        '''
        [SEL_ID, IDX_ID, IP_ID, PORT_ID, SN_ID, STATE_ID, DEPLOY_PROGRESS, NAME_ID]
        '''
        DebugLog.debug_print_level1("in server controller update_server_password")
        server_data = self.getServerData(server_id)
        
        params = [server_data[NAME_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(POWERONSERVER), server_data[IDX_ID], params)  #"UPDATE_PASSWD"
        self._sendMsg2CommCnt(msg)
        
        #self.get_server_current_status()  
    
    
    def recover_server_profile(self, server_id):
        DebugLog.debug_print_level1("in server controller recoverprofile")
        server_data = self.getServerData(server_id)
        params = [server_data[NAME_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(RECOVERPROFILE), server_data[IDX_ID], params)  #"recoverprofile"
        self._sendMsg2CommCnt(msg, delayed=True)
        

    def poweronserver(self, server_id):
#         DebugLog.debug_print_level1("in server controller poweronserver")
#         ckecked_items_id_list = self.getCheckedItemsIdList()
#         for item_id in range(len(ckecked_items_id_list)):
#             server_data = ckecked_items_id_list[item_id]
        server_data = self.getServerData(server_id)
        params = [server_data[NAME_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(POWERONSERVER), server_data[IDX_ID], params)  #"POWERON"
        self._sendMsg2CommCnt(msg) 
            

    def create_vios_lpar(self, server_id):
        DebugLog.debug_print_level1("in server controller createvioslpar")
        server_data = self.getServerData(server_id)
        params = [server_data[NAME_ID], server_data[SN_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(CREATEVIOSLPAR), server_data[IDX_ID], params)  #"POWERON"
        self._sendMsg2CommCnt(msg)
                        
        
    def nimserver_prepare_host_file(self, server_id):
        server_data = self.getServerData(server_id)
        params = [server_data[IP_FOR_NIMINSTALL], server_data[SN_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(PREPAREHOSTSFILE), server_data[IDX_ID], params)  #"POWERON"
        self._sendMsg2CommCnt(msg)
            
            
    def nimserver_define_nim_host(self, server_id):
        DebugLog.debug_print_level1("in server controller createvioslpar")
#         ckecked_items_id_list = self.getCheckedItemsIdList()
#         for item_id in range(len(ckecked_items_id_list)):
        server_data = self.getServerData(server_id)
        params = [server_data[SN_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(DEFINESERVER), server_data[IDX_ID], params)  #"POWERON"
        self._sendMsg2CommCnt(msg) 
            
            
    def nim_allocat_resource(self, server_id):
        DebugLog.debug_print_level1("in server controller nim_allocat_resource")
        server_data = self.getServerData(server_id)
        params = [server_data[SN_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(ASSIGNRESOURCE), server_data[IDX_ID], params)  #"POWERON"
        self._sendMsg2CommCnt(msg)
            
            
    def poweroffserver(self, server_id):
        DebugLog.debug_print_level1("in server controller poweroffserver")
        server_data = self.getServerData(server_id)
        params = [server_data[NAME_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(POWEROFFSERVER), server_data[IDX_ID], params)  #"POWEROFF"
        self._sendMsg2CommCnt(msg)
            
            
    def hmc_poweroff_server(self, server_id):
        '''
        [SEL_ID, IDX_ID, IP_ID, PORT_ID, SN_ID, STATE_ID, DEPLOY_PROGRESS, NAME_ID]
        '''
        DebugLog.debug_print_level1("in server controller hmc_poweroff_server")
        server_data = self.getServerData(server_id)
        params = [server_data[NAME_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(POWEROFFSERVER), server_data[IDX_ID], params)  #"UPDATE_PASSWD"
        self._sendMsg2CommCnt(msg)
        
        
    def remove_nonhmc_connection(self, server_id):
        DebugLog.debug_print_level1("in server remove no-hmc connection")
        server_data = self.getServerData(server_id)
        params = [server_data[IP_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(RMV_NON_HMC), server_data[IDX_ID], params)  #"POWEROFF"
        self._sendMsg2CommCnt(msg)
        
        
    def asm_poweron(self, server_id):
        DebugLog.debug_print_level1("in server asm poweron")
        server_data = self.getServerData(server_id)
        params = [server_data[IP_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(ASM_POWERON), server_data[IDX_ID], params)  #"POWEROFF"
        self._sendMsg2CommCnt(msg)
        
        
    def installsw(self, server_id):
        DebugLog.debug_print_level1("in server install powerdirector")
        server_data = self.getServerData(server_id)
        params = [server_data[IP_FOR_NIMINSTALL]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(INSTALLSW), server_data[IDX_ID], params)  #"POWEROFF"
        self._sendMsg2CommCnt(msg)
        
    
    def set_default_ip(self, server_id):
        DebugLog.debug_print_level1("in server set default ip")
        server_data = self.getServerData(server_id)
        params = [server_data[SN_ID], server_data[IP_FOR_NIMINSTALL]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(SET_DEFAULT_IP), server_data[IDX_ID], params)
        self._sendMsg2CommCnt(msg)
            

    def set_default_ip_and_shutdown(self, server_id):
        DebugLog.debug_print_level1("in server set default ip and shutdown function")
        server_data = self.getServerData(server_id)
        params = [server_data[SN_ID], server_data[IP_FOR_NIMINSTALL]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(SET_DEFAULT_IP_AND_SHUTDOWN), server_data[IDX_ID], params)
        self._sendMsg2CommCnt(msg)
                    
        
    def remove_server_from_hmc(self, server_id):
        DebugLog.debug_print_level1("in server controller remove_server_from_hmc")
        server_data = self.getServerData(server_id)
        params = [server_data[IP_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(REMVSERVER), server_data[IDX_ID], params)  #"POWEROFF"
        self._sendMsg2CommCnt(msg)
                     

    def install_vios_server(self, server_id):
        DebugLog.debug_print_level1("in server controller install_vios_server")
        server_data = self.getServerData(server_id)
        key_pairs = {}
        key_pairs['name_server_ip'] = self.config.get('topo', 'nimserver_ip')
        key_pairs['gateway'] = self.config.get('nimserver_ip_pool', 
                                               'ip_pool_gateway_ip')
        
        key_pairs['client_ip'] = server_data[IP_FOR_NIMINSTALL]
        key_pairs['server_sn'] = server_data[SN_ID]
        key_pairs['server_prf'] = '%sprf' % server_data[SN_ID]
        key_pairs['server_name'] = server_data[NAME_ID]
        
        params = [key_pairs]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(INSTALLVIOS), server_data[IDX_ID], params)  #"POWEROFF"
        self._sendMsg2CommCnt(msg)
            
    
    def hmc2ivm_rst_fw_factory_settings(self, server_id):
        server_data = self.getServerData(server_id)
        params = [server_data[IP_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(RST_FW_FCTRY), server_data[IDX_ID], params)  #"POWEROFF"
        self._sendMsg2CommCnt(msg)


    def clean_nim_resource(self, server_id):
        DebugLog.debug_print_level1("in server controller clean_nim_resource")
        server_data = self.getServerData(server_id)
        params = [server_data[SN_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(CLEANNIMRESOURCE), server_data[IDX_ID], params)  #"POWEROFF"
        self._sendMsg2CommCnt(msg)
        
    
    def check_nim_resource_clean(self, server_id):
        DebugLog.debug_print_level1("in server controller check_nim_resource_clean")
        server_data = self.getServerData(server_id)
        
        params = [server_data[SN_ID]]
        msg = self.msg_coder.encodeMsg(CMDMsg.getCMD(CHECKCLEANSTATUS), server_data[IDX_ID], params)
        self._sendMsg2CommCnt(msg)
        

    def launch_state_task(self, state_idx):
        ckecked_items_id_list = self.getCheckedItemsIdList()
        for item_id in range(len(ckecked_items_id_list)):
            server_data = ckecked_items_id_list[item_id]
            fsm_manager = self.fsm_manager[int(server_data[IDX_ID])]
            phase = StateBase.get_state_const(state_idx)
            progress = StateBase.get_state_progress_const_name(PRGRS_READY)  # server_data[PROGRESS]
#            expected_states = fsm_manager.get_next_states()
#             if not phase in expected_states:
#                 tkMessageBox.showinfo("State Exception", u"执行的动作不是期望的")
#                 raise ActionIsNotExpected_Exception()
            fsm_manager.setTaskState(phase, progress)
            

    def server_task_start(self, msg):
        '''
        For one click button to server installation task
        '''
        _cmd, _idx, _data = self.msg_coder.decodeMsg(msg)
        tmp = eval(_data)
        server_id = tmp[0]
        _bPause = tmp[1]
        server_details_info = self.getServerData(server_id)
        _server_cur_phase_str = server_details_info[PHASE]
        fsm_manager = self.fsm_manager[int(server_details_info[IDX_ID])]
        
        if _bPause:
            fsm_manager.auto_mode = False
            return 
        else:
            fsm_manager.auto_mode = True
        
        if CMDMsg.getCMD(INSTALL_VIOS_ONLY) == _cmd:
            fsm_manager.update_states_order()
            DebugLog.info_print("install vios only update states order")
            
        phase_state = fsm_manager.get_cur_state(_server_cur_phase_str)
        #phase = StateBase.get_state_const(PASSWORD_REQUIRED_STAT)
        phase = phase_state.get_next_state().get_state_name()
        
        progress = StateBase.get_state_progress_const_name(PRGRS_READY)
        DebugLog.info_print("Set Task %d as %s %s" % (server_id, phase, progress))
        #fsm_manager.setTaskState(phase, progress)
        self.start_server_in_fsm_manager(server_id, phase, progress)
            
                    
    def start_eng(self):
            
        #hello_eng = HelloEng()
        self.hmc_eng = HMCEng(self.communicate_center, self.config)
        self.asmi_eng = AsmiEng(self.communicate_center)
        self.nimserver_eng = NIMEng(self.communicate_center, self.config)
        self.server_eng = ServerEng(self.communicate_center, self.config)
        
        cmd_msgs_handlers = \
            [(CMDMsg.getCMD(SERVERSCAN),            self.hmc_eng.process_message,       self.updateData),
             (CMDMsg.getCMD(UPDATEPASSWD),          self.hmc_eng.process_message,       self.updateData),
             (CMDMsg.getCMD(CHECKUPDATEPASSWD),     self.hmc_eng.process_message,       self.updateData),
             (CMDMsg.getCMD(REMVSERVER),            self.hmc_eng.process_message,       self.updateData),
             (CMDMsg.getCMD(CHECKREMVSERVER),       self.hmc_eng.process_message,       self.updateData),
             (CMDMsg.getCMD(POWEROFFSERVER),        self.hmc_eng.process_message,       self.updateData),
             (CMDMsg.getCMD(CHECKPOWEROFFSERVER),   self.hmc_eng.process_message,       self.updateData),
             (CMDMsg.getCMD(GETSTATUS),             self.hmc_eng.process_message,       self.updateData),
             (CMDMsg.getCMD(RECOVERPROFILE),        self.hmc_eng.process_message,       self.updateData),
             (CMDMsg.getCMD(CHECKRECOVERPROFILE),   self.hmc_eng.process_message,       self.updateData),
             (CMDMsg.getCMD(POWERONSERVER),         self.hmc_eng.process_message,       self.updateData),
             (CMDMsg.getCMD(CHECKPOWERONSERVER),    self.hmc_eng.process_message,       self.updateData),
             
             (CMDMsg.getCMD(CREATEVIOSLPAR),        self.hmc_eng.process_message,       self.updateData),
             (CMDMsg.getCMD(CHECKCREATEVIOSLPAR),   self.hmc_eng.process_message,       self.updateData),
             (CMDMsg.getCMD(PREPAREHOSTSFILE),      self.nimserver_eng.process_message, self.updateData),
             (CMDMsg.getCMD(CHECKHOSTSFILE),        self.nimserver_eng.process_message, self.updateData),
             (CMDMsg.getCMD(DEFINESERVER),          self.nimserver_eng.process_message, self.updateData),
             (CMDMsg.getCMD(CHECKDEFINEDSERVER),    self.nimserver_eng.process_message, self.updateData),
             (CMDMsg.getCMD(ASSIGNRESOURCE),        self.nimserver_eng.process_message, self.updateData),
             (CMDMsg.getCMD(CHECKASSIGNEDRESOURCE), self.nimserver_eng.process_message, self.updateData),
             
             (CMDMsg.getCMD(INSTALLVIOS),           self.hmc_eng.process_message,       self.updateData),
             (CMDMsg.getCMD(CHECKVIOSINSTALL),      self.server_eng.process_message,    self.updateData),
             
             (CMDMsg.getCMD(CLEANNIMRESOURCE),      self.nimserver_eng.process_message, self.updateData),
             (CMDMsg.getCMD(CHECKCLEANSTATUS),      self.nimserver_eng.process_message, self.updateData),
             (CMDMsg.getCMD(ACCEPTLICENSE),         self.server_eng.process_message,    self.updateData),
             (CMDMsg.getCMD(CHECKACCEPTLICENSE),    self.server_eng.process_message,    self.updateData),
             
             (CMDMsg.getCMD(RST_FW_FCTRY),          self.asmi_eng.process_message,      self.updateData),
             (CMDMsg.getCMD(CHECKRST_FW_FCTRY),     self.asmi_eng.process_message,      self.updateData),
             (CMDMsg.getCMD(RMV_NON_HMC),           self.asmi_eng.process_message,      self.updateData),
             (CMDMsg.getCMD(CHECKRMV_NON_HMC),      self.asmi_eng.process_message,      self.updateData),
             (CMDMsg.getCMD(ASM_POWERON),           self.asmi_eng.process_message,      self.updateData),
             (CMDMsg.getCMD(CHECKASM_POWERON),      self.server_eng.process_message,    self.updateData),
             (CMDMsg.getCMD(INSTALLSW),             self.server_eng.process_message,    self.updateData),
             (CMDMsg.getCMD(SET_DEFAULT_IP),        self.server_eng.process_message,    self.updateData),
             (CMDMsg.getCMD(SET_DEFAULT_IP_AND_SHUTDOWN),        self.server_eng.process_message,    self.updateData),
             (CMDMsg.getCMD(UPDATESTATUS),          None,                               self.updateData),
             (CMDMsg.getCMD(AUTOSTART),             self.server_task_start,             None),
             (CMDMsg.getCMD(INSTALL_VIOS_ONLY),     self.server_task_start,             None),                            
             ]
        
        
        for m,n,p in cmd_msgs_handlers:
            self.communicate_center.register_msg_handler(m, n, p)

    
