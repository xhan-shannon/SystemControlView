#--*-- coding:utf-8 --*--
'''
Created on 2015��5��19��

@author: stm
'''
from utils import DebugLog
from base.cmdmsg import CMDMsg, SERVERSCAN, INSTALLVIOS, UPDATEPASSWD,\
    RECOVERPROFILE, POWERONSERVER, CREATEVIOSLPAR, PREPAREHOSTSFILE, DEFINESERVER,\
    ASSIGNRESOURCE, REMVSERVER, RST_FW_FCTRY, RMV_NON_HMC,\
    POWEROFFSERVER, ACCEPTLICENSE, CLEANNIMRESOURCE, ASM_POWERON, INSTALLSW,\
    SET_DEFAULT_IP, SET_DEFAULT_IP_AND_SHUTDOWN

 
STATE_NAME_L = ["VD_READY",
                CMDMsg.getCMD(SERVERSCAN),
                "Pending Authentication - Password Updates Required",
                "Failed Authentication",
                CMDMsg.getCMD(UPDATEPASSWD),
                "Recovery",
                CMDMsg.getCMD(RECOVERPROFILE),
                "Power Off",
                CMDMsg.getCMD(POWERONSERVER),
                "Operating",
                "Standby",
                
                #"INSTALL_VIOS",
                CMDMsg.getCMD(CREATEVIOSLPAR),
                CMDMsg.getCMD(PREPAREHOSTSFILE),
                CMDMsg.getCMD(DEFINESERVER),
                CMDMsg.getCMD(ASSIGNRESOURCE),
                CMDMsg.getCMD(INSTALLVIOS),
                CMDMsg.getCMD(CLEANNIMRESOURCE),
                CMDMsg.getCMD(ACCEPTLICENSE),
                #
                CMDMsg.getCMD(SET_DEFAULT_IP),
                #
                CMDMsg.getCMD(POWEROFFSERVER),
                CMDMsg.getCMD(REMVSERVER),
                CMDMsg.getCMD(RST_FW_FCTRY),
                CMDMsg.getCMD(RMV_NON_HMC),
                CMDMsg.getCMD(ASM_POWERON),
                 
                CMDMsg.getCMD(INSTALLSW),
                CMDMsg.getCMD(SET_DEFAULT_IP_AND_SHUTDOWN),
                #"HMC2IVM_REMOVE_NON_HMC_CONNECTION",
                #"HMC2IVM_POWERON",
                #"REGISTER_PD",
                "VD_END",
                 ]
 
(VD_READY, \
 SERVERSCAN_STAT, PASSWORD_REQUIRED_STAT, FAILED_AUTH_STAT, \
 UPDATEPASSWD_STAT, RECOVERY_STAT, RECOVERPROFILE_STAT, \
 POWEROFF_STAT, POWERONSERVER_STAT, \
 OPERATING_STAT, STANDBY_STAT, \
 CREATEVIOSLPAR_STAT, PREPAREHOSTSFILE_STAT, DEFINESERVER_STAT, ASSIGNRESOURCE_STAT, \
 INSTALL_VIOS_STAT, CLEAN_NIM_RESOURCE_STAT, ACCEPTLICENSE_STAT, \
 SET_DEFAULT_IP_STAT, \
 POWEROFFSERVER_STAT, REMVSERVER_STAT, RST_FW_FCTRY_STAT, RMV_NON_HMC_STAT, \
 #REGISTER_PD, \
 ASM_POWERON_STAT, INSTALLSW_STAT, SET_DEFAULT_IP_AND_SHUTDOWN_STAT, \
 VD_END) = range(len(STATE_NAME_L))
 
PROGRESS_VAL = ["READY",
                "STARTED",
                "INPROGRESS",
                "FINISHED"]
(PRGRS_READY, PRGRS_STARTED, PRGRS_INPROGRESS, 
PRGRS_FINISHED) = range(len(PROGRESS_VAL))


class StateBase(object):
    '''
    Basic Finite State Machine class represent the status and the related function needs
    to be executed to change to the next state
    '''
    def __init__(self, state_name, obj_func):
        self.state_name = state_name
        #self.next_state_name = next_state_name
        self.state_act = obj_func
        self.state_before_intalling = True
        self.next_state_list = []
        self.check_status_handlers = []
        
    def enter_state(self):
        DebugLog.info_print("enter state: %s" % self.state_name)
    
    def state_act(self, param):
        raise NotImplementedError()
    
    
    def checkStateStatus(self):
        raise NotImplementedError()
    
    
    def exit_state(self):
        DebugLog.info_print("exit state: %s" % self.state_name)
    
    def get_state_name(self):
        return self.state_name
    
    def get_internal_auto(self):
        return self.state_before_intalling
    
    
    def set_checkStatus(self, state_check_handler):
        #self.check_status_handlers.append(state_check_handler)
        self.checkStateStatus = state_check_handler
        
    def set_state_act(self, state_act):
        self.state_act = state_act
        
    def get_next_states(self):
        state_desc_list = []
        for obj in self.next_state_list:
            state_desc_list.append(obj.get_state_name())
            
        return state_desc_list
    
    def get_next_state(self):
        '''
        To the next state for the current state
        '''
        return self.next_state_list[0]

    
    def set_next_state(self, state):
        self.next_state_list.append(state)
        
    
    def clear_next_state(self):
        self.next_state_list = []
        
    @staticmethod
    def get_state_const(idx):
        return STATE_NAME_L[idx]
    
    @staticmethod
    def get_state_progress_const_name(idx):
        return PROGRESS_VAL[idx]
    
    @staticmethod
    def get_state_name_idx(state_name):
        '''return the idx value of the state'''
        idx = -1
        for _state_name in STATE_NAME_L:
            idx += 1
            if _state_name == state_name:
                return idx
        
        
class Start_State(StateBase):
    '''
    VD Task start state
    '''
    def __init__(self, obj_func):
        StateBase.__init__(self, 
                         STATE_NAME_L[VD_READY], 
                         obj_func)
        
        
class End_State(StateBase):
    '''
    VD Task end state
    '''
    def __init__(self):
        StateBase.__init__(self, 
                         STATE_NAME_L[VD_END],
                         None)
        
    
class Server_Scan_State(StateBase):
    '''Server Scan state'''
    def __init__(self, obj_func):
        StateBase.__init__(self,
                           STATE_NAME_L[SERVERSCAN_STAT], 
                           obj_func)
        
        
class Authentication_Password_Required_State(StateBase):
    '''Authentication Password Required state'''
    def __init__(self, obj_func):
        StateBase.__init__(self, 
                         STATE_NAME_L[PASSWORD_REQUIRED_STAT],
                         obj_func)
        
    
class Failed_Authentication_State(StateBase):
    '''Failed Authentication state'''
    def __init__(self,  obj_func):
        StateBase.__init__(self, 
                         STATE_NAME_L[FAILED_AUTH_STAT],
                         obj_func)
        

class UpdatePassword_State(StateBase):
    '''Update password State'''
    def __init__(self, obj_func):
        StateBase.__init__(self,
                           STATE_NAME_L[UPDATEPASSWD_STAT], 
                           obj_func)
        
            
class Recovery_State(StateBase):
    '''Recovery state'''
    def __init__(self,  obj_func):
        StateBase.__init__(self,
                           STATE_NAME_L[RECOVERY_STAT],
                           obj_func)
        
class RecoveryProfile_State(StateBase):
    '''Recovery profile state'''
    def __init__(self,  obj_func):
        StateBase.__init__(self,
                           STATE_NAME_L[RECOVERPROFILE_STAT],
                           obj_func)
        

class PowerOff_State(StateBase):
    '''Server power off state'''
    def __init__(self,  obj_func):
        StateBase.__init__(self,
                           STATE_NAME_L[POWEROFF_STAT],
                           obj_func)
    

class PowerOnServer_State(StateBase):
    '''Power on a Server power state'''
    def __init__(self,  obj_func):
        StateBase.__init__(self,
                           STATE_NAME_L[POWERONSERVER_STAT],
                           obj_func)
        
class Operating_State(StateBase):
    '''Operating state'''
    def __init__(self,  obj_func):
        StateBase.__init__(self, 
                         STATE_NAME_L[OPERATING_STAT], 
                         obj_func)
        

class Standby_State(StateBase):
    '''Standby state'''
    def __init__(self,  obj_func):
        StateBase.__init__(self, 
                         STATE_NAME_L[STANDBY_STAT], 
                         obj_func)           
                

class CreateViosLpar_State(StateBase):
    '''Create vios lpar state'''
    def __init__(self,obj_func):
        StateBase.__init__(self,
                         STATE_NAME_L[CREATEVIOSLPAR_STAT], 
                         obj_func)
        self.state_before_intalling = False 
        

class PrepareHostsFile_State(StateBase):
    '''Prepare Hosts File state'''
    def __init__(self,obj_func):
        StateBase.__init__(self,
                         STATE_NAME_L[PREPAREHOSTSFILE_STAT], 
                         obj_func)
        self.state_before_intalling = False 
        
                
class DefineServer_State(StateBase): 
    ''' Hmc2ivm Reset Factory Setttings state'''
    def __init__(self,obj_func):
        StateBase.__init__(self,
                         STATE_NAME_L[DEFINESERVER_STAT], 
                         obj_func) 
        self.state_before_intalling = False


class AssignResource_State(StateBase):
    '''Hmc2ivm Remove Non Hmc Connection state'''
    def __init__(self,obj_func):
        StateBase.__init__(self,
                         STATE_NAME_L[ASSIGNRESOURCE_STAT], 
                         obj_func) 
        self.state_before_intalling = False
        
        
class InstallVios_State(StateBase):
    '''install vios state'''
    def __init__(self,obj_func):
        StateBase.__init__(self,
                         STATE_NAME_L[INSTALL_VIOS_STAT], 
                         obj_func) 
        self.state_before_intalling = False
        

class CleanNimResource_State(StateBase):
    '''clean vios nim resource state'''
    def __init__(self,obj_func):
        StateBase.__init__(self,
                         STATE_NAME_L[CLEAN_NIM_RESOURCE_STAT], 
                         obj_func) 
        self.state_before_intalling = False
        

class Set_DefaultIP_State(StateBase):
    '''Set Default IP state'''
    def __init__(self,obj_func):
        StateBase.__init__(self,
                         STATE_NAME_L[SET_DEFAULT_IP_STAT], 
                         obj_func) 
        self.state_before_intalling = False    
        
                
class PowerOff_Server_State(StateBase):
    '''Power off server state'''
    def __init__(self,obj_func):
        StateBase.__init__(self,
                         STATE_NAME_L[POWEROFFSERVER_STAT], 
                         obj_func) 
        self.state_before_intalling = False
        

class Remove_Server_State(StateBase):
    '''remove server from hmc state'''
    def __init__(self,obj_func):
        StateBase.__init__(self,
                         STATE_NAME_L[REMVSERVER_STAT], 
                         obj_func) 
        self.state_before_intalling = False
        
        
class Reset_Fw_Factory_State(StateBase):
    '''
    reset fw factory state
    '''
    def __init__(self,obj_func):
        StateBase.__init__(self,
                         STATE_NAME_L[RST_FW_FCTRY_STAT], 
                         obj_func) 
        self.state_before_intalling = False
        
            
class Remove_Non_Hmc_connection_State(StateBase):
    '''remove non hmc connection in asmi state'''
    def __init__(self,obj_func):
        StateBase.__init__(self,
                         STATE_NAME_L[RMV_NON_HMC_STAT], 
                         obj_func) 
        self.state_before_intalling = False
        
        
class Asm_Poweron_State(StateBase):
    '''
    reset fw factory state
    '''
    def __init__(self,obj_func):
        StateBase.__init__(self,
                         STATE_NAME_L[ASM_POWERON_STAT], 
                         obj_func) 
        self.state_before_intalling = False
        
        
class Accept_License_State(StateBase):
    '''Accept license state'''
    def __init__(self,obj_func):
        StateBase.__init__(self,
                         STATE_NAME_L[ACCEPTLICENSE_STAT], 
                         obj_func) 
        self.state_before_intalling = False        
        
        
class Install_SW_State(StateBase):
    '''Install preinstallation software state'''
    def __init__(self,obj_func):
        StateBase.__init__(self,
                         STATE_NAME_L[INSTALLSW_STAT], 
                         obj_func) 
        self.state_before_intalling = False    
    

        
        
class Set_DefaultIP_And_Shutdown_State(StateBase):
    '''Set Default IP state'''
    def __init__(self,obj_func):
        StateBase.__init__(self,
                         STATE_NAME_L[SET_DEFAULT_IP_AND_SHUTDOWN_STAT], 
                         obj_func) 
        self.state_before_intalling = False    
    
                            
class Vd_Finished_State(StateBase):
    '''Vd Finished state'''
    def __init__(self,obj_func):
        StateBase.__init__(self,
                         STATE_NAME_L[VD_END], 
                         obj_func) 
        
        
# class FSM_Manager(object):
#     '''FSM manager'''
#     def __init__(self):
#         self._fsms= {}
#         self._fsms[STATE_NAME_L[PASSWORD_REQUIRED_STAT]]   = Authentication_Password_Required_State(None)
#         self._fsms[STATE_NAME_L[FAILED_AUTH_STAT]]         = Failed_Authentication_State(None)
#         self._fsms[STATE_NAME_L[SERVER_SCAN_RECOVERY_STAT]]            = Recovery_State(None)
#         self._fsms[STATE_NAME_L[OPERATING_STAT]]           = Operating_State(None)
#         self._fsms[STATE_NAME_L[STANDBY_STAT]]             = Standby_State(None)
#         self._fsms[STATE_NAME_L[SERVER_SCAN_POWER_OFF_STAT]]           = Poweroff_State(None)
#         self._fsms[STATE_NAME_L[INSTALL_VIOS]]                         = Instlingvios_State(None)
#         self._fsms[STATE_NAME_L[HMC2IVM_RESET_FACTORY_SETTTINGS]]      = Hmc2ivm_Reset_Factory_Setttings_State(None)
#         self._fsms[STATE_NAME_L[HMC2IVM_REMOVE_NON_HMC_CONNECTION]]    = Hmc2ivm_Remove_Non_Hmc_Connection_State(None)
#         self._fsms[STATE_NAME_L[HMC2IVM_POWERON]]                      = Hmc2ivm_Poweron_State(None)
#         self._fsms[STATE_NAME_L[REGISTER_PD]]                          = Register_Pd_State(None)
#         self._fsms[STATE_NAME_L[VD_END]]                          = Vd_Finished_State(None)
#         
#         self._current_state = 0
#         self._new_state = 0
#         self._init = False
#         self._inprogressing = False
#         
# 
#     
#     def set_stat_func(self, state_id, func):
#         
#         state_fsm_obj =  None
#         if VD_READY == state_id:
#             state_fsm_obj = self._fsms[STATE_NAME_L[PASSWORD_REQUIRED_STAT]]
#         elif PASSWORD_REQUIRED_STAT == state_id:
#             state_fsm_obj = self._fsms[STATE_NAME_L[PASSWORD_REQUIRED_STAT]]
#         elif FAILED_AUTH_STAT == state_id:
#             state_fsm_obj = self._fsms[STATE_NAME_L[FAILED_AUTH_STAT]]
#         elif SERVER_SCAN_RECOVERY_STAT == state_id:
#             state_fsm_obj = self._fsms[STATE_NAME_L[SERVER_SCAN_RECOVERY_STAT]]
#         elif OPERATING_STAT == state_id:
#             state_fsm_obj = self._fsms[STATE_NAME_L[OPERATING_STAT]]
#         elif STANDBY_STAT == state_id:
#             state_fsm_obj = self._fsms[STATE_NAME_L[STANDBY_STAT]]
#         elif SERVER_SCAN_POWER_OFF_STAT == state_id:
#             state_fsm_obj = self._fsms[STATE_NAME_L[SERVER_SCAN_POWER_OFF_STAT]]
#         elif INSTALL_VIOS == state_id:
#             state_fsm_obj = self._fsms[STATE_NAME_L[INSTALL_VIOS]]
#         elif HMC2IVM_RESET_FACTORY_SETTTINGS == state_id:
#             state_fsm_obj = self._fsms[STATE_NAME_L[HMC2IVM_RESET_FACTORY_SETTTINGS]]
#         elif HMC2IVM_REMOVE_NON_HMC_CONNECTION == state_id:
#             state_fsm_obj = self._fsms[STATE_NAME_L[HMC2IVM_REMOVE_NON_HMC_CONNECTION]]
#         elif HMC2IVM_POWERON == state_id:
#             state_fsm_obj = self._fsms[STATE_NAME_L[HMC2IVM_POWERON]]
#         elif REGISTER_PD == state_id:
#             state_fsm_obj = self._fsms[STATE_NAME_L[REGISTER_PD]]
#         elif VD_END == state_id:
#             state_fsm_obj = None   
#         
#         if state_fsm_obj:
#             state_fsm_obj.state_act = func
#             
#         
#     
#     def launch_act(self, state, param):
#         fsm_state = self.get_state(state)
#         if fsm_state and fsm_state.state_act:
#             fsm_state.state_act(param)
#             
# 
#     
#     def get_state_count(self):
#         return len(self._fsms.keys())
#     
#     
#     def get_state(self, state_key):
#         try:
#             fsm_state = self._fsms[state_key]
#         except:
#             fsm_state = None
#             
#         return fsm_state
#     
#     
#     def set_state(self, new_state, data):
#         if not self._init:
#             self._current_state = new_state
#             
#         if self._current_state == new_state:
#             if not self._inprogressing:
#                 self._inprogressing = True
#                 self.launch_act(new_state, data)
#         else:
#             self._inprogressing = False         
#             self._current_state = new_state
            