#--*-- coding:utf-8 --*--
'''
Created on 2015��6��1��

@author: stm
'''
import time
from base.vdstate import Start_State, STATE_NAME_L, VD_READY,\
    Failed_Authentication_State, Recovery_State, Operating_State,\
    Server_Scan_State, SERVERSCAN_STAT, Authentication_Password_Required_State,\
    PASSWORD_REQUIRED_STAT, FAILED_AUTH_STAT,\
    UPDATEPASSWD_STAT, RECOVERY_STAT, RECOVERPROFILE_STAT, UpdatePassword_State,\
    RecoveryProfile_State, POWEROFF_STAT, PowerOff_State, POWERONSERVER_STAT,\
    PowerOnServer_State, OPERATING_STAT, STANDBY_STAT, ASM_POWERON_STAT, \
    Standby_State, PREPAREHOSTSFILE_STAT, CREATEVIOSLPAR_STAT,\
    CreateViosLpar_State, PrepareHostsFile_State, DEFINESERVER_STAT,\
    ASSIGNRESOURCE_STAT, DefineServer_State, INSTALL_VIOS_STAT,\
    AssignResource_State, InstallVios_State, POWEROFFSERVER_STAT,\
    REMVSERVER_STAT, RST_FW_FCTRY_STAT, PowerOff_Server_State,\
    Remove_Server_State, Remove_Non_Hmc_connection_State, RMV_NON_HMC_STAT,\
    End_State, VD_END, Reset_Fw_Factory_State, StateBase, PRGRS_FINISHED, \
    PRGRS_INPROGRESS, PRGRS_READY, Accept_License_State, ACCEPTLICENSE_STAT, \
    CLEAN_NIM_RESOURCE_STAT, CleanNimResource_State, Asm_Poweron_State, ASM_POWERON_STAT, \
    INSTALLSW_STAT, SET_DEFAULT_IP_STAT, Install_SW_State, Set_DefaultIP_State,\
    SET_DEFAULT_IP_AND_SHUTDOWN_STAT, Set_DefaultIP_And_Shutdown_State
    
from threading import Thread
from utils import DebugLog
from utils.FileLock import FileLock

IN_PROGRESS = " in progress "
FINISHED = " Finished ."
class CoreTask(object):
    '''
    The core task in VD
    '''

    def __init__(self, task_id):
        '''
        Constructor
        '''
        self.cur_phase = None
        self.state_act = None
        self.checkStateStatus = None
        self.check_loop = 0
        self.auto_mode = False
        self.state_progress = ''
        self.inprogress = False
        self._f_go_to_next = False
        self.task_id = task_id
        
        self.initVdStates()
    

    def get_cur_state(self, cur_state_info):
        return self._fsms[cur_state_info]
    
    def get_next_states(self):
        states_lst = []
        if self.cur_phase:
            states_lst = self.get_cur_state(self.cur_phase).get_next_states()
        return states_lst

 
    def _goto_auto(self):
        def _delay_exec_call(sec):
            time.sleep(sec)
            if self.auto_mode:
                DebugLog.info_print("In the auto mode, to launch next state")
                phase_state = self.get_cur_state(self.cur_phase)
                phase = phase_state.get_next_state().get_state_name()
                
                DebugLog.info_print("Server idx: %s, goto next phase: %s " % 
                                    (self.task_id, phase))
                if StateBase.get_state_const(VD_END) == phase:
                    progress = StateBase.get_state_progress_const_name(PRGRS_FINISHED)
                else:
                    progress = StateBase.get_state_progress_const_name(PRGRS_READY)
                self.setTaskState(phase, progress)
            
        DebugLog.info_print("At _goto_auto function")       
        _delay_call_thrd = Thread(target=lambda delay_secs=3: _delay_exec_call(delay_secs))
        _delay_call_thrd.start()
                            
                               
    def test_if_can_goto_next(self):
        bResult = self._f_go_to_next            
        return bResult
    
    
    def disable_goto_next(self):
        self._f_go_to_next = False
 
    def enable_goto_next(self):
        self._f_go_to_next = True
                       
    
    
    def _goto_auto_with_lock(self):
        lock_file  = "set_gotonext_file_%d.lock" % self.task_id
        with FileLock(lock_file, timeout=300):
            if self.test_if_can_goto_next():
                self.disable_goto_next()
                self._goto_auto()
    
    
    def setTaskState(self, phase, progress, first=False):
        '''
        Set task state to launch the state method
        '''
        if not self.cur_phase and progress.strip() == '':
            return
        
#         if self.cur_phase and self.cur_phase == phase:
#             return
                   
        if first:
            if not self.cur_phase:
                self.cur_phase = phase
                #self.state_progress = phase + " finished ."
                self.state_progress = FINISHED
        else:
            if StateBase.get_state_name_idx(phase) < StateBase.get_state_name_idx(self.cur_phase):
                return
            DebugLog.info_print("Set Task %d as %s %s" % (self.task_id, phase, progress))
            if not (phase == self.cur_phase):
                self.cur_phase = phase
            self.state_obj = self._fsms[phase]
            if StateBase.get_state_progress_const_name(PRGRS_READY) == progress:
                if self.state_obj.state_act and not self.inprogress:
                    self.inprogress = True
                    self.enable_goto_next()
                    
                    _phase_act_thrd = Thread(target=lambda idx=self.task_id: self.state_obj.state_act(idx))
                    _phase_act_thrd.start()
#                 else:
#                     if self.state_obj.checkStateStatus:
#                         _phase_chk_thrd = Thread(target=lambda idx=self.task_id: self.state_obj.checkStateStatus(idx))
#                         _phase_chk_thrd.start()
                self.state_progress =  IN_PROGRESS
                #self.state_progress =  " in progress "

            elif StateBase.get_state_progress_const_name(PRGRS_INPROGRESS) == progress:                      
                if self.state_obj.checkStateStatus:
                    _phase_chk_thrd = Thread(target=lambda idx=self.task_id: self.state_obj.checkStateStatus(idx))
                    _phase_chk_thrd.start()
    
                #self.state_progress =  phase + IN_PROGRESS
                                           
            elif StateBase.get_state_progress_const_name(PRGRS_FINISHED) == progress:
                #self.state_progress = phase + " finished ." 
                self.state_progress = FINISHED
                
                if self.inprogress:
                    self.inprogress = False
                
                    if StateBase.get_state_name_idx(self.cur_phase) >= CREATEVIOSLPAR_STAT:
                        self._goto_auto_with_lock()                     
                else:                    
                    if StateBase.get_state_name_idx(self.cur_phase) < CREATEVIOSLPAR_STAT:
                        self._goto_auto_with_lock()
                        
                    

    def getTaskPhase(self):
        return self.cur_phase                
         
        
    def getTaskStateProgress(self):
        _state_progress_surfix = ""
        if self.inprogress:
            _state_progress_surfix = "."*(self.check_loop+1)
            self.check_loop += 1
            self.check_loop = self.check_loop % 3
        return self.state_progress + " %s" % _state_progress_surfix
        
        
    def initVdStates(self):
        self._fsms= {}
        self._fsms[STATE_NAME_L[VD_READY]]                          = Start_State(None)
        
        self._fsms[STATE_NAME_L[SERVERSCAN_STAT]]                   = Server_Scan_State(None)
        self._fsms[STATE_NAME_L[PASSWORD_REQUIRED_STAT]]            = Authentication_Password_Required_State(None)
        self._fsms[STATE_NAME_L[FAILED_AUTH_STAT]]                  = Failed_Authentication_State(None)
        self._fsms[STATE_NAME_L[UPDATEPASSWD_STAT]]                 = UpdatePassword_State(None)
        self._fsms[STATE_NAME_L[RECOVERY_STAT]]                     = Recovery_State(None)
        self._fsms[STATE_NAME_L[RECOVERPROFILE_STAT]]               = RecoveryProfile_State(None)
        self._fsms[STATE_NAME_L[POWEROFF_STAT]]                     = PowerOff_State(None)
        self._fsms[STATE_NAME_L[POWERONSERVER_STAT]]                = PowerOnServer_State(None)
        self._fsms[STATE_NAME_L[OPERATING_STAT]]                    = Operating_State(None)
        self._fsms[STATE_NAME_L[STANDBY_STAT]]                      = Standby_State(None)
        self._fsms[STATE_NAME_L[CREATEVIOSLPAR_STAT]]               = CreateViosLpar_State(None)
        self._fsms[STATE_NAME_L[PREPAREHOSTSFILE_STAT]]             = PrepareHostsFile_State(None)
        self._fsms[STATE_NAME_L[DEFINESERVER_STAT]]                 = DefineServer_State(None)
        self._fsms[STATE_NAME_L[ASSIGNRESOURCE_STAT]]               = AssignResource_State(None)
        self._fsms[STATE_NAME_L[INSTALL_VIOS_STAT]]                 = InstallVios_State(None)
        self._fsms[STATE_NAME_L[CLEAN_NIM_RESOURCE_STAT]]           = CleanNimResource_State(None)
        self._fsms[STATE_NAME_L[ACCEPTLICENSE_STAT]]                = Accept_License_State(None)
        self._fsms[STATE_NAME_L[SET_DEFAULT_IP_STAT]]               = Set_DefaultIP_State(None)                                 
        self._fsms[STATE_NAME_L[POWEROFFSERVER_STAT]]               = PowerOff_Server_State(None)
        self._fsms[STATE_NAME_L[REMVSERVER_STAT]]                   = Remove_Server_State(None)
        self._fsms[STATE_NAME_L[RST_FW_FCTRY_STAT]]                 = Reset_Fw_Factory_State(None)
        self._fsms[STATE_NAME_L[RMV_NON_HMC_STAT]]                  = Remove_Non_Hmc_connection_State(None)
        self._fsms[STATE_NAME_L[ASM_POWERON_STAT]]                  = Asm_Poweron_State(None)
        self._fsms[STATE_NAME_L[INSTALLSW_STAT]]                    = Install_SW_State(None)
        self._fsms[STATE_NAME_L[SET_DEFAULT_IP_AND_SHUTDOWN_STAT]]  = Set_DefaultIP_And_Shutdown_State(None)                                 

        self._fsms[STATE_NAME_L[VD_END]]                       = End_State()
        
        for key in self._fsms.keys():
            _state_obj = self._fsms[key] 
            if STATE_NAME_L[VD_READY] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[SERVERSCAN_STAT]])
            elif STATE_NAME_L[SERVERSCAN_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[PASSWORD_REQUIRED_STAT]])
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[FAILED_AUTH_STAT]])

            elif STATE_NAME_L[PASSWORD_REQUIRED_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[UPDATEPASSWD_STAT]])

                                                         
            elif STATE_NAME_L[FAILED_AUTH_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[UPDATEPASSWD_STAT]])

            elif STATE_NAME_L[UPDATEPASSWD_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[RECOVERY_STAT]])
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[POWEROFF_STAT]])
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[OPERATING_STAT]])
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[STANDBY_STAT]])
                                                                
            elif STATE_NAME_L[RECOVERY_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[RECOVERPROFILE_STAT]])
#                 _state_obj.set_next_state(self._fsms[STATE_NAME_L[OPERATING_STAT]])
#                 _state_obj.set_next_state(self._fsms[STATE_NAME_L[STANDBY_STAT]])
                
            elif STATE_NAME_L[RECOVERPROFILE_STAT] == key:
                #_state_obj.set_next_state(self._fsms[STATE_NAME_L[OPERATING_STAT]])
                #_state_obj.set_next_state(self._fsms[STATE_NAME_L[STANDBY_STAT]])
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[CREATEVIOSLPAR_STAT]])
 
            elif STATE_NAME_L[POWEROFF_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[POWERONSERVER_STAT]])

            elif STATE_NAME_L[POWERONSERVER_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[UPDATEPASSWD_STAT]])                                 
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[RECOVERY_STAT]])
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[OPERATING_STAT]])
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[STANDBY_STAT]])
                                                                
            elif STATE_NAME_L[OPERATING_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[CREATEVIOSLPAR_STAT]])
#                 _state_obj.set_next_state(self._fsms[STATE_NAME_L[INSTALL_VIOS_STAT]])
#                 _state_obj.set_next_state(self._fsms[STATE_NAME_L[ACCEPTLICENSE_STAT]])
#                 _state_obj.set_next_state(self._fsms[STATE_NAME_L[CLEAN_NIM_RESOURCE_STAT]])
#                 _state_obj.set_next_state(self._fsms[STATE_NAME_L[REMVSERVER_STAT]])
                           
            elif STATE_NAME_L[STANDBY_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[CREATEVIOSLPAR_STAT]])
#                 _state_obj.set_next_state(self._fsms[STATE_NAME_L[INSTALL_VIOS_STAT]])
#                 _state_obj.set_next_state(self._fsms[STATE_NAME_L[ACCEPTLICENSE_STAT]])

            elif STATE_NAME_L[CREATEVIOSLPAR_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[PREPAREHOSTSFILE_STAT]])

            elif STATE_NAME_L[PREPAREHOSTSFILE_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[DEFINESERVER_STAT]])

            elif STATE_NAME_L[DEFINESERVER_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[ASSIGNRESOURCE_STAT]])

            elif STATE_NAME_L[ASSIGNRESOURCE_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[INSTALL_VIOS_STAT]])

            elif STATE_NAME_L[INSTALL_VIOS_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[CLEAN_NIM_RESOURCE_STAT]])

            elif STATE_NAME_L[CLEAN_NIM_RESOURCE_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[ACCEPTLICENSE_STAT]])
                
            elif STATE_NAME_L[ACCEPTLICENSE_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[POWEROFFSERVER_STAT]])

            elif STATE_NAME_L[POWEROFFSERVER_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[REMVSERVER_STAT]])

            elif STATE_NAME_L[REMVSERVER_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[RST_FW_FCTRY_STAT]])

            elif STATE_NAME_L[RST_FW_FCTRY_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[RMV_NON_HMC_STAT]])

            elif STATE_NAME_L[RMV_NON_HMC_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[ASM_POWERON_STAT]])
                
            elif STATE_NAME_L[ASM_POWERON_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[INSTALLSW_STAT]])
                
            elif STATE_NAME_L[INSTALLSW_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[SET_DEFAULT_IP_AND_SHUTDOWN_STAT]])
                
            elif STATE_NAME_L[SET_DEFAULT_IP_AND_SHUTDOWN_STAT] == key:
                _state_obj.set_next_state(self._fsms[STATE_NAME_L[VD_END]])
                
            else:
                pass
                
                
    def set_states_acts(self, state_id, func):
        _state_obj = self._fsms[STATE_NAME_L[state_id]]
        _state_obj.set_state_act(func)
        
    def set_status_check_handler(self, state_id, handler):
        _state_obj = self._fsms[STATE_NAME_L[state_id]]
        _state_obj.set_checkStatus(handler)
        
    def get_state_count(self):
        return len(self._fsms.keys())


    def update_states_order(self):
        _state_obj = self._fsms[STATE_NAME_L[ACCEPTLICENSE_STAT]]
        _state_obj.clear_next_state()
        _state_obj.set_next_state(self._fsms[STATE_NAME_L[SET_DEFAULT_IP_STAT]])
        
        _state_obj = self._fsms[STATE_NAME_L[SET_DEFAULT_IP_STAT]]
        _state_obj.clear_next_state()
        _state_obj.set_next_state(self._fsms[STATE_NAME_L[POWEROFFSERVER_STAT]])
        
        _state_obj = self._fsms[STATE_NAME_L[RMV_NON_HMC_STAT]]
        _state_obj.clear_next_state()
        _state_obj.set_next_state(self._fsms[STATE_NAME_L[VD_END]])
                        
