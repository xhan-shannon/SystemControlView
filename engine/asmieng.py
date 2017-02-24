#--*-- coding:utf-8 --*--
'''
Created on 2015��5��14��

@author: stm
'''
from base.engine import EngineBase
from utils import DebugLog
from base.cmdmsg import CMDMsg, RST_FW_FCTRY, RMV_NON_HMC, ASM_POWERON
from engine.asmi import ASMi
from base.vdstate import StateBase,PRGRS_INPROGRESS, PRGRS_FINISHED, RMV_NON_HMC_STAT, RST_FW_FCTRY_STAT, ASM_POWERON_STAT


class AsmiEng(EngineBase):
    '''
    classdocs
    '''


    def __init__(self, vd_comm_cnt):
        '''
        Constructor
        '''
        DebugLog.info_print("ASMiEng initialized")
        EngineBase.__init__(self, vd_comm_cnt, None)
        

    def hmc2ivm(self, data):
        '''
        as for data is a list type, deal with the server for each ip
        @data: list type which contains server's name
        '''
        
        data_list = eval(data)
        loop_cnt = len(data_list)
        for loop_idx in range(loop_cnt):
            server_ip = data_list[loop_idx]
            asmi_client = ASMi(server_ip)
            try:
                sn = asmi_client.get_serial_number()
                DebugLog.info_print("Get the serial number for the target %s is : %s"
                                % (server_ip, sn))
                asmi_client.login()
                asmi_client.reset_server_firmware_settings()
    
                asmi_client.reset_server_to_non_HMC(server_ip)
                asmi_client.get_power_on_off_continue_button().click()
            finally:
                asmi_client.logout()
                
                
    def save_settings(self,server_id,data):
        data_list = eval(data)
        loop_cnt = len(data_list)
        for loop_idx in range(loop_cnt):
            server_ip = data_list[loop_idx]
            asmi_client = ASMi(server_ip)
        sn = asmi_client.get_serial_number()
        DebugLog.info_print("Get the serial number for the target %s is : %s"
                                % (server_ip, sn))
        asmi_client.login()
        asmi_client.savesettings()
                
                
    def ams_remove_connection(self, server_id,data):
        data_list = eval(data)
        loop_cnt = len(data_list)
        for loop_idx in range(loop_cnt):
            server_ip = data_list[loop_idx]
            asmi_client = ASMi(server_ip)
        sn = asmi_client.get_serial_number()
        DebugLog.info_print("Get the serial number for the target %s is : %s"
                                % (server_ip, sn))
        asmi_client.login()
        asmi_client.reset_server_to_non_HMC(server_ip)
        
        resp_state = [StateBase.get_state_const(RMV_NON_HMC_STAT), 
                      StateBase.get_state_progress_const_name(PRGRS_FINISHED)]
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(RMV_NON_HMC),
                                         server_id,
                                         resp_state)
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
        
        
    def ams_poweron(self,server_id,data):
        data_list = eval(data)
        loop_cnt = len(data_list)
        for loop_idx in range(loop_cnt):
            server_ip = data_list[loop_idx]
            asmi_client = ASMi(server_ip)
        sn = asmi_client.get_serial_number()
        DebugLog.info_print("Get the serial number for the target %s is : %s"
                            % (server_ip, sn))
        asmi_client.login()
        asmi_client.poweron()
        resp_state = [StateBase.get_state_const(ASM_POWERON_STAT), 
                      StateBase.get_state_progress_const_name(PRGRS_INPROGRESS)]
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(ASM_POWERON),
                                         server_id,
                                         resp_state)
            
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
        
               

    def reset_server_firmware_settings(self,server_id,data):
        data_list = eval(data)
        loop_cnt = len(data_list)
        for loop_idx in range(loop_cnt):
            server_ip = data_list[loop_idx]
            asmi_client = ASMi(server_ip)
        sn = asmi_client.get_serial_number()
        DebugLog.info_print("Get the serial number for the target %s is : %s"
                            % (server_ip, sn))
        asmi_client.login()
        asmi_client.reset_server_firmware_settings()
        
        resp_state = [StateBase.get_state_const(RST_FW_FCTRY_STAT), 
                      StateBase.get_state_progress_const_name(PRGRS_FINISHED)]
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(RST_FW_FCTRY),
                                         server_id,
                                         resp_state)
            
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
        
    
    def process_message(self, msg):
        DebugLog.debug_print_level1("Got the command tranfering in asmi engine")
        cmd, _server_id, data = self.msg_decoder.decodeMsg(msg)
#         if CMDMsg.getCMD(HMCTOIVM) == cmd:
#             self.hmc2ivm(data)
        if CMDMsg.getCMD(RST_FW_FCTRY) == cmd:
            self.reset_server_firmware_settings(_server_id, data)
        elif CMDMsg.getCMD(RMV_NON_HMC) == cmd:
            self.save_settings(_server_id, data)
            self.ams_remove_connection(_server_id, data)
        elif CMDMsg.getCMD(ASM_POWERON) == cmd:
            self.ams_poweron(_server_id, data)

#                 # acess
#         # 2. access the target ip browser, poweroff the target
# 
#         asmi_client = ASMi(target_ip)
#         sn = asmi_client.get_serial_number()
#         DebugLog.info_print("Get the serial number for the target %s is : %s"
#                             % (target_ip, sn))
#         asmi_client.login()
# 
#         # check if the ivm host power on
#         power_status = asmi_client.get_power_status()
#         if 'On' == power_status:
#             asmi_client.expand_power_restart_control_link()
#             asmi_client.click_immediate_power_off_link()
#             time.sleep(1)
#             asmi_client.click_continue_button()
# 
#         # To check if the ivm host go to power off status
#         iCount = 0
#         while iCount < 10:
#             # do something
#             DebugLog.info_print("Getting the power status of the IVM host")
#             power_status = asmi_client.get_power_status()
#             DebugLog.info_print("The current power status is: %s" % power_status)
#             if 'Off' == power_status:
#                 DebugLog.info_print("Already goes into the power off status")
#                 break
# 
#             time.sleep(2)
#             iCount += 1
# 
# 
#         asmi_client.reset_server_firmware_settings()
# 
#         # asmi_client.get_realtime_progress_indicator_link_status()
# 
# #         iCount = 0
# #
# #         while iCount < 10:
# #             DebugLog.info_print("To test if there is new browser page")
# #             gotit = asmi_client.get_power_on_off_continue_button()
# #             if gotit:
# #                 DebugLog.info_print("Got the continue button")
# #                 break
# #             else:
# #                 DebugLog.info_print("Still not got the continue button, try again")
# #
# #             time.sleep(2)
# #
# 
#         asmi_client.reset_server_to_non_HMC(target_ip)
#         asmi_client.logout()