#--*-- coding:utf-8 --*--
'''
Created on 2015��5��8��

@author: stm
'''

from base.cmdmsg import SERVERSCAN, GETSTATUS, UPDATEPASSWD, \
                        REMVSERVER, POWEROFFSERVER, RECOVERPROFILE, \
                        POWERONSERVER, RMV_NON_HMC, CREATEVIOSLPAR, \
                        CHECKCREATEVIOSLPAR, INSTALLVIOS, CHECKPOWERONSERVER,\
    CHECKUPDATEPASSWD, CHECKRECOVERPROFILE, UPDATESTATUS, CHECKPOWEROFFSERVER
from base.engine import EngineBase
from sessions.hmccli_session import HMC_CLI
import string


from utils import DebugLog
from utils.ErrorHandler import ConfigFileError
from base.cmdmsg import CMDMsg
from base.vdstate import PRGRS_INPROGRESS, CREATEVIOSLPAR_STAT, StateBase,\
    PRGRS_FINISHED, PASSWORD_REQUIRED_STAT, FAILED_AUTH_STAT, RECOVERY_STAT,\
    OPERATING_STAT, STANDBY_STAT, UPDATEPASSWD_STAT, POWERONSERVER_STAT,\
    POWEROFF_STAT, RECOVERPROFILE_STAT, PRGRS_READY, INSTALL_VIOS_STAT,\
    REMVSERVER_STAT, POWEROFFSERVER_STAT
import time


class HMCEng(EngineBase):
    '''
    classdocs
    '''

    def __init__(self, vd_comm_cnt, vd_config):
        DebugLog.info_print("HMCEng initialized")
        EngineBase.__init__(self, vd_comm_cnt, vd_config)
        
        try:
            self.hmc_ip = self.vd_config.get('topo', 'hmc_ip')
            self.hmc_passwd = self.vd_config.get('topo', 'hmc_passwd')
        except:
            raise ConfigFileError()
            
    def server_scan(self):
        '''
        establish session with hmc 
        issue ip scan action to collect the results -F name,ipaddr,serial_num,state
        '''
        hmc_cli = HMC_CLI(self.hmc_ip, self.hmc_passwd)
        resp = hmc_cli.server_scan()
        
        if isinstance(resp, list):
            result_list = resp
        else:
            result_list = string.split(resp, '\n')
            
        if not result_list:
            result_list = [',,,']
        DebugLog.info_print(str(resp))
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(SERVERSCAN), '_', result_list)
        self.vd_comm_cnt.postMessage(msg)
        
        
    def getCurrentStatus(self):
        '''
        establish session with hmc 
        issue ip scan action to collect the results
        '''
        hmc_cli = HMC_CLI(self.hmc_ip, self.hmc_passwd)
        resp = hmc_cli.get()
        
        if isinstance(resp, list):
            result_list = resp
        else:
            result_list = string.split(resp, '\n')
        DebugLog.info_print(str(resp))
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(SERVERSCAN), result_list)
        self.vd_comm_cnt.postMessage(msg)
    
    
    def update_password(self, server_id, data):
        '''
        update password for the vios machine which is from data list
        @data: list type
        '''
        self._deal_with_data(server_id, data, "update_password")
        
        DebugLog.debug_print_level1("Connect hmc client session, update_password")
        resp_state = [StateBase.get_state_const(UPDATEPASSWD_STAT), 
                      StateBase.get_state_progress_const_name(PRGRS_INPROGRESS)]
        
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(UPDATEPASSWD),
                                         server_id, 
                                         resp_state)
        
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
        
            
    def recover_server_profile(self, server_id, data):
        '''
        recover server profile for the vios machine which is from data list
        @data: list type which contains server's name
        '''
        DebugLog.debug_print_level1("Connect hmc client session, recover_server_profile")
        resp_state = [StateBase.get_state_const(RECOVERPROFILE_STAT), 
                      StateBase.get_state_progress_const_name(PRGRS_INPROGRESS)]
        
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(RECOVERPROFILE),
                                         server_id, 
                                         resp_state)
        
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
        self._deal_with_data(server_id, data, "recover_profile")
        
        
    def remove_server_from_hmc(self, server_id, data):        
        '''
        remove server profile for the vios machine which is from data list
        @data: list type which contains server's name
        '''
        DebugLog.debug_print_level1("Connect hmc client session, remove_server_from_hmc")
        resp_state = [StateBase.get_state_const(REMVSERVER_STAT), 
                      StateBase.get_state_progress_const_name(PRGRS_INPROGRESS)]
        
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(REMVSERVER),
                                         server_id, 
                                         resp_state)
        
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
#         hmc_cli = HMC_CLI(self.hmc_ip, self.hmc_passwd)
#         data_list = eval(data)
#         loop_cnt = len(data_list)
#         for loop_idx in range(loop_cnt):
#             hmc_cli.remove_hmc_connection(data_list[loop_idx])
        self._deal_with_data(server_id, 
                             data, 
                             "remove_hmc_connection", 
                             with_params=True, 
                             post_cmd=None)
        
        resp_state = [StateBase.get_state_const(REMVSERVER_STAT), 
                      StateBase.get_state_progress_const_name(PRGRS_FINISHED)]
        
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(REMVSERVER),
                                         server_id, 
                                         resp_state)
        
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
    
    
    def _deal_with_data(self, server_id, data, func, with_params=True, post_cmd=None):
        '''
        as for data is a list type, and let func to deal with all the data
        @data: list type which contains server's name
        '''
        DebugLog.debug_print_level1("Connect hmc client session")
        hmc_cli = HMC_CLI(self.hmc_ip, self.hmc_passwd)
        data_list = eval(data)
        loop_cnt = len(data_list)
        for loop_idx in range(loop_cnt):
            func_name = "hmc_cli."+func
            DebugLog.debug_print_level1("Call hmc client function %s" % func_name)
            if with_params:
                resp = eval(func_name)(data_list[loop_idx])
            else:
                resp = eval(func_name)()
                
            if post_cmd:
                msg = self.msg_decoder.encodeMsg(post_cmd, server_id, resp)
                DebugLog.debug_print_level1(msg)
                self.vd_comm_cnt.postMessage(msg)
    
    
    def poweroffserver(self, server_id, data):
        ''' power off the server using the server's name which in the data list'''
        DebugLog.debug_print_level1("Connect hmc client session, poweroffserver")
        resp_state = [StateBase.get_state_const(POWEROFFSERVER_STAT), 
                      StateBase.get_state_progress_const_name(PRGRS_INPROGRESS)]
        
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(POWEROFFSERVER),
                                         server_id, 
                                         resp_state)
        
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
        self._deal_with_data(server_id, data, "poweroff_server")
    
    
    def poweronserver(self, server_id, data):
        ''' power on the server using the server's name which in the data list'''
        DebugLog.debug_print_level1("Connect hmc client session, poweronserver")
        resp_state = [StateBase.get_state_const(POWERONSERVER_STAT), 
                      StateBase.get_state_progress_const_name(PRGRS_INPROGRESS)]
        
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(POWERONSERVER),
                                         server_id, 
                                         resp_state)
        
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
        self._deal_with_data(server_id, data, "poweron_server")
        
        
    def createvioslpar(self, server_id, data):
        ''' create vios lpar on the server using the server's name which in the data list'''
        DebugLog.debug_print_level1("Connect hmc client session")
        resp_state = [StateBase.get_state_const(CREATEVIOSLPAR_STAT), 
                      StateBase.get_state_progress_const_name(PRGRS_INPROGRESS)]
        
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(CREATEVIOSLPAR),
                                         server_id, 
                                         resp_state)
        
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
        
        hmc_cli = HMC_CLI(self.hmc_ip, self.hmc_passwd)
        data = eval(data)
        server_slots = hmc_cli.get_server_slots(data[0])
        server_slots = '//0,'.join(server_slots)
        DebugLog.debug_print_level1("Get server slots %s" % server_slots)
        data_params = []
        data_params.append(data[0])
        data_params.append(data[1])
        data_params.append(server_slots)
        
        data = []
        data.append(data_params)
        self._deal_with_data(server_id, str(data), "create_vios_lpar")
        

        
        
    def check_if_create_vios_lpar_state(self, server_id, server_name, server_sn):
        '''
        '''
        hmc_cli = HMC_CLI(self.hmc_ip, self.hmc_passwd)
        ret = hmc_cli.check_if_create_vios_lpar_finished(server_name,
                                                         server_sn)
        
        resp_state = None
        
        count = 1
#         while not ret:
#             
        if ret:
            resp_state = [StateBase.get_state_const(CREATEVIOSLPAR_STAT), 
                          StateBase.get_state_progress_const_name(PRGRS_FINISHED)]
        else:
            resp_state = [StateBase.get_state_const(CREATEVIOSLPAR_STAT), 
                          StateBase.get_state_progress_const_name(PRGRS_INPROGRESS)]
            #count = (count + 1) % 4 

        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(CHECKCREATEVIOSLPAR),
                                         server_id, 
                                         resp_state)
            
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
    
        
        
    def install_vios(self, server_id, data):
        '''install a vios'''
        DebugLog.debug_print_level1("Connect hmc client session")
        resp_state = [StateBase.get_state_const(INSTALL_VIOS_STAT), 
                      StateBase.get_state_progress_const_name(PRGRS_INPROGRESS)]
        
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(INSTALLVIOS),
                                         server_id, 
                                         resp_state)
        
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
        DebugLog.debug_print_level1("Connect hmc client session")
        self._deal_with_data(server_id, str(data), "lpar_net_boot")
        
        
    def check_poweron_status(self, server_id, data):
        hmc_cli = HMC_CLI(self.hmc_ip, self.hmc_passwd)
        data = eval(data)
        _server_name = data[0]
        status_ret = hmc_cli.get_server_status(_server_name)
        
        poweron_status_list = [StateBase.get_state_const(PASSWORD_REQUIRED_STAT),
                               StateBase.get_state_const(FAILED_AUTH_STAT),
                               StateBase.get_state_const(UPDATEPASSWD_STAT),
                               StateBase.get_state_const(RECOVERY_STAT),
                               StateBase.get_state_const(OPERATING_STAT),
                               StateBase.get_state_const(STANDBY_STAT),
                               ]
        
        poweron_val = False
        if status_ret[0] in poweron_status_list:
            poweron_val = True
        
        if poweron_val:
            resp_state = [StateBase.get_state_const(POWERONSERVER_STAT), 
                          StateBase.get_state_progress_const_name(PRGRS_FINISHED)]
        else:
            resp_state = [StateBase.get_state_const(POWERONSERVER_STAT), 
                          StateBase.get_state_progress_const_name(PRGRS_INPROGRESS)]

        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(POWERONSERVER),
                                         server_id, 
                                         resp_state)
            
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)

        if poweron_val:
            self.get_server_hmc_status(server_id, _server_name)
            

    def check_poweroff_status(self, server_id, data):
        hmc_cli = HMC_CLI(self.hmc_ip, self.hmc_passwd)
        data = eval(data)
        _server_name = data[0]
        status_ret = hmc_cli.get_server_status(_server_name)
        
        poweroff_status_list = [StateBase.get_state_const(POWEROFF_STAT),
                               ]
        
        poweroff_val = False
        if status_ret[0] in poweroff_status_list:
            poweroff_val = True
        
        if poweroff_val:
            resp_state = [StateBase.get_state_const(POWEROFFSERVER_STAT), 
                          StateBase.get_state_progress_const_name(PRGRS_FINISHED)]
        else:
            resp_state = [StateBase.get_state_const(POWEROFFSERVER_STAT), 
                          StateBase.get_state_progress_const_name(PRGRS_INPROGRESS)]

        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(POWEROFFSERVER),
                                         server_id, 
                                         resp_state)
            
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
        
        
    def getstatus(self):
        '''get the specified server status using the server's name which in the data list'''
        self._deal_with_data(0, '["0"]', "get_managed_sys_info", 
                             with_params=False, 
                             post_cmd=CMDMsg.getCMD(GETSTATUS))
        
    
    def get_server_hmc_status_by_serial_num(self, server_id, serial_num):
        '''get the specified server status using the server's name which in the data list'''
        DebugLog.debug_print_level1("Connect hmc client session")
        hmc_cli = HMC_CLI(self.hmc_ip, self.hmc_passwd)
        _server_name = hmc_cli.get_server_name_by_sn(serial_num)
        self.get_server_hmc_status(server_id, _server_name)
        
            
    def get_server_hmc_status(self, server_id, _server_name):
        '''get the specified server status using the server's name which in the data list'''
        DebugLog.debug_print_level1("Connect hmc client session")
        hmc_cli = HMC_CLI(self.hmc_ip, self.hmc_passwd)
        
        ret = hmc_cli.get_server_status_and_name(_server_name)
        _server_status, _server_name = ret[0].split(",")
        resp_state = [_server_status, 
                      StateBase.get_state_progress_const_name(PRGRS_FINISHED),
                      _server_name]
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(UPDATESTATUS), server_id, resp_state)
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)

    
    
    def check_UpdatePassword_Status(self, _server_id, data):
        '''
        To check the update password process is finished.
        '''
        hmc_cli = HMC_CLI(self.hmc_ip, self.hmc_passwd)
        data = eval(data)
        _serial_num = data[0]
        _server_name = hmc_cli.get_server_name_by_sn(_serial_num)
        status_ret = hmc_cli.get_server_status(_server_name)
        DebugLog.debug_print_level1(str(status_ret))
        updatepasswd_check_status_list = [
                               StateBase.get_state_const(POWEROFF_STAT),
                               StateBase.get_state_const(RECOVERY_STAT),
                               StateBase.get_state_const(OPERATING_STAT),
                               StateBase.get_state_const(STANDBY_STAT),
                               ]
        
        update_password_finished = False
        if status_ret[0] in updatepasswd_check_status_list:
            update_password_finished = True
        
        if update_password_finished:
            resp_state = [StateBase.get_state_const(UPDATEPASSWD_STAT), 
                          StateBase.get_state_progress_const_name(PRGRS_FINISHED)]
        else:
            resp_state = [StateBase.get_state_const(UPDATEPASSWD_STAT), 
                          StateBase.get_state_progress_const_name(PRGRS_INPROGRESS)]
            #count = (count + 1) % 4 

        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(UPDATEPASSWD),
                                         _server_id, 
                                         resp_state)
            
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
        
        if update_password_finished:
            self.get_server_hmc_status(_server_id, _server_name)
            
    
    
    def check_recover_profile_status(self, _server_id, data):
        hmc_cli = HMC_CLI(self.hmc_ip, self.hmc_passwd)
        data = eval(data)
        _server_name = data[0]
        status_ret = hmc_cli.get_server_status(_server_name)
        
        recoverprofile_check_status_list = [
                               StateBase.get_state_const(POWEROFF_STAT),
                               StateBase.get_state_const(OPERATING_STAT),
                               StateBase.get_state_const(STANDBY_STAT),
                               ]
        
        recover_profile_finished = False
        if status_ret[0] in recoverprofile_check_status_list:
            recover_profile_finished = True
        
        if recover_profile_finished:
            resp_state = [StateBase.get_state_const(RECOVERPROFILE_STAT), 
                          StateBase.get_state_progress_const_name(PRGRS_FINISHED)]
        else:
            resp_state = [StateBase.get_state_const(RECOVERPROFILE_STAT), 
                          StateBase.get_state_progress_const_name(PRGRS_INPROGRESS)]
            #count = (count + 1) % 4 

        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(RECOVERPROFILE),
                                         _server_id, 
                                         resp_state)
            
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
        
        if recover_profile_finished:
            self.get_server_hmc_status(_server_id, _server_name)
    
    
    def process_message(self, msg):
        DebugLog.debug_print_level1("Got the command tranfering in hmc engine")
        cmd, _server_id, data = self.msg_decoder.decodeMsg(msg)
        if CMDMsg.getCMD(SERVERSCAN) == cmd:
            self.server_scan()
        elif CMDMsg.getCMD(UPDATEPASSWD) == cmd:
            self.update_password(_server_id, data)
        elif CMDMsg.getCMD(CHECKUPDATEPASSWD) == cmd:
            self.check_UpdatePassword_Status(_server_id, data)
        elif CMDMsg.getCMD(REMVSERVER) == cmd:
            self.remove_server_from_hmc(_server_id, data)
        elif CMDMsg.getCMD(POWEROFFSERVER) == cmd:
            self.poweroffserver(_server_id, data)
        elif CMDMsg.getCMD(CHECKPOWEROFFSERVER) == cmd:
            self.check_poweroff_status(_server_id, data)        
        elif CMDMsg.getCMD(GETSTATUS) == cmd:
            self.getstatus()
        elif CMDMsg.getCMD(RECOVERPROFILE) == cmd:
            self.recover_server_profile(_server_id, data)
        #CHECKRECOVERPROFILE
        elif CMDMsg.getCMD(CHECKRECOVERPROFILE) == cmd:
            self.check_recover_profile_status(_server_id, data)
        elif CMDMsg.getCMD(POWERONSERVER) == cmd:
            self.poweronserver(_server_id, data)
        elif CMDMsg.getCMD(CHECKPOWERONSERVER) == cmd:
            self.check_poweron_status(_server_id, data)
        elif CMDMsg.getCMD(CREATEVIOSLPAR) == cmd:
            self.createvioslpar(_server_id, data)
        elif CMDMsg.getCMD(INSTALLVIOS) == cmd:
            self.install_vios(_server_id, data)
        elif CMDMsg.getCMD(CHECKCREATEVIOSLPAR) == cmd:
            _server_name, _server_sn = eval(data)
            self.check_if_create_vios_lpar_state(_server_id, 
                                                 _server_name, 
                                                 _server_sn)