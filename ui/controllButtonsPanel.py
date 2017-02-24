#--*-- coding:utf-8 --*--
'''
Created on 2015��5��9��

@author: stm
'''

from Tkinter import Frame, Button
import Tkinter
from Tkconstants import TOP, LEFT, RIGHT
from utils import DebugLog
import time
from ui.BasePanel import BasePanel
from base.cmdmsg import SERVERSCAN, UPDATEPASSWD, CMDMsg,  \
    CREATEVIOSLPAR, CREATEVIOSLPAR, DEFINESERVER, PREPAREHOSTSFILE, INSTALLVIOS, \
    ASSIGNRESOURCE,  REMVSERVER, RMV_NON_HMC, RST_FW_FCTRY,  INSTALLSW, SHOWRECORDS, \
    POWERONSERVER, POWEROFFSERVER, RECOVERPROFILE, GETSTATUS, SAVESELECTION\
    , ACCEPTLICENSE, CLEANNIMRESOURCE, SET_DEFAULT_IP, ASM_POWERON
from base.msgcodec import MsgCodec
from engine.asmieng import AsmiEng
from base.vdstate import PASSWORD_REQUIRED_STAT, RECOVERPROFILE_STAT,\
    POWERONSERVER_STAT, CREATEVIOSLPAR_STAT, DEFINESERVER_STAT,\
    ASSIGNRESOURCE_STAT, INSTALL_VIOS_STAT, POWEROFFSERVER_STAT, REMVSERVER_STAT,\
    RST_FW_FCTRY_STAT, RMV_NON_HMC_STAT, PREPAREHOSTSFILE_STAT,\
    UPDATEPASSWD_STAT, ACCEPTLICENSE_STAT, CLEAN_NIM_RESOURCE_STAT, INSTALLSW_STAT, \
    SET_DEFAULT_IP_STAT, ASM_POWERON_STAT


class ControlButtonsPanel(BasePanel):
    '''
    classdocs
    '''

    def hello_test(self):
        DebugLog.debug_print_level1("in hello callback")

        msg = "hello: 'How are you?'"
        self.controller.sendMsg2CommCnt(msg)

    
    def server_scan(self):
        DebugLog.debug_print_level1("in server_scan button callback")
        self.controller.server_scan()
    
    
    def getCheckedMachineList(self):
        checked_ids_list = self.appl.getSelectedMachnineName()
        return checked_ids_list
    
    
    def getCheckedItemsIdList(self):
        checked_ids_list = self.appl.getSelectedMachnineName()
        return checked_ids_list
    
    
    def updatepasswd(self):
        DebugLog.debug_print_level1("in updatepasswd button callback")      
        self.controller.update_password()
        
        
    def recoverprofile(self):
        DebugLog.debug_print_level1("in recoverprofile button callback")      
        self.controller.recover_server_profile()
    
    
    def getSelectedServerIPs(self):
        checked_ids_list = self.appl.getSelectedMachnineIP()
        return checked_ids_list
    
    
    def remove_connection(self):
        DebugLog.debug_print_level1("in remove connection button callback")
        self.controller.remove_nonhmc_connection()
        
    
    
    def remove_server_from_hmc(self):
        DebugLog.debug_print_level1("in updatepasswd button callback")
        self.controller.remove_server_from_hmc()
    

    def poweroffsvr(self):
        DebugLog.debug_print_level1("in poweroff server button callback")
        self.controller.poweroffserver()
        
    
    def poweronsvr(self):
        DebugLog.debug_print_level1("in poweron server button callback")
        self.controller.poweronserver()
        
        
    def create_vioslpar(self):
        DebugLog.debug_print_level1("in create vios lpar button callback")
        self.controller.createvioslpar()
    
    
    def get_current_status(self):
        DebugLog.debug_print_level1("in get_current_status button callback")      
        self.controller.get_server_current_status()

    
    def hmc2ivm_rst_fw_factory_settings(self):
        '''
        for those selected server, reset to factory settings in firware
        '''
        DebugLog.debug_print_level1("in hmc2ivm_rst_fw_factory_settings button callback")
        self.controller.hmc2ivm_rst_fw_factory_settings()


#         for svrip in checked_ip_list:
#             asmi_eng = AsmiEng(None, svrip)
#             asmi_eng.reset_server_firmware_settings()

    
    
    def showhidePanel(self):
        self.appl.getControlButtonsPanel().pack_forget()
        self.appl.getMainPanel().showHidePanel()
    
    
    def prepare_host_file(self):
        '''
        for those selected server, add to nim server hosts file
        '''
        DebugLog.debug_print_level1("in prepare_host_file button callback")
        self.controller.nimserver_prepare_host_file()
    
    
    def define_nim_host(self):
        '''
        for those selected server, add to nim server hosts file
        '''
        DebugLog.debug_print_level1("in nim_define_nim_host button callback")
        self.controller.nimserver_define_nim_host()
    
    
    def nim_allocat_resource(self):
        '''
        for those selected server, allocate resource for the server
        '''
        DebugLog.debug_print_level1("in nim_allocat_resource button callback")
        self.controller.nim_allocat_resource()
    
    
    def install_vios(self):
        '''
        for those selected server, allocate resource for the server
        '''
        DebugLog.debug_print_level1("in install_vios button callback")
        self.controller.install_vios()
    
    
    
    def launch_state_task(self, idx):
        self.controller.launch_state_task(idx)
    
    
    def showhidebtns(self):
        self.cntl_btns_visible = not self.cntl_btns_visible
        
        if self.cntl_btns_visible: 
            for panel in self.cntl_btns_panel:
                panel.pack_forget()              
            for btn in self.cntl_btns:
                btn.pack()
        else:
            for panel in self.cntl_btns_panel:
                panel.pack()
            for btn in self.cntl_btns:
                btn.pack()
                

                
    
    
    def createWidgets(self):      
       
        first_row = Frame(self)
        second_row = Frame(self)
        third_row = Frame(self)
        fourth_row = Frame(self)
        widget_height = 2
        widget_width = 27
        #auto_btn = Tkinter.Button(first_row, text="AUTO", width=widget_width, height=widget_height)
#        manual_btn = Button(first_row, text="Manual", width="15", height=widget_height)
        
        ipscan_btn              = Button(first_row, text="%d:" % (SERVERSCAN + 1) + CMDMsg.getCmdDesc(SERVERSCAN),
                                         width=widget_width, height=widget_height)
        update_passwd_btn       = Button(first_row, text="%d:" % (UPDATEPASSWD + 1) + CMDMsg.getCmdDesc(UPDATEPASSWD), 
                                        width=widget_width, height=widget_height)
        recover_profile_btn     = Button(first_row, text="%d:" % (RECOVERPROFILE + 1) + CMDMsg.getCmdDesc(RECOVERPROFILE), 
                                        width=widget_width, height=widget_height)
        power_on_svr_btn        = Button(first_row, text="%d:" % (POWERONSERVER + 1) + CMDMsg.getCmdDesc(POWERONSERVER),
                                         width=widget_width, height=widget_height)
        create_vios_lpar_btn    = Button(second_row, text="%d:" % (CREATEVIOSLPAR + 1) + CMDMsg.getCmdDesc(CREATEVIOSLPAR),
                                         width=widget_width, height=widget_height)
        prepare_hosts_file_btn  = Button(second_row, text="%d:" % (PREPAREHOSTSFILE + 1) + CMDMsg.getCmdDesc(PREPAREHOSTSFILE),
                                         width=widget_width, height=widget_height)
        define_nim_host_btn     = Button(second_row, text="%d:" % (DEFINESERVER + 1) + CMDMsg.getCmdDesc(DEFINESERVER),
                                         width=widget_width, height=widget_height)
        allocate_sources_btn    = Button(second_row, text="%d:" % (ASSIGNRESOURCE + 1) + CMDMsg.getCmdDesc(ASSIGNRESOURCE),
                                         width=widget_width, height=widget_height)
        install_vios_btn        = Button(second_row, text="%d:" % (INSTALLVIOS + 1) + CMDMsg.getCmdDesc(INSTALLVIOS),
                                         width=widget_width, height=widget_height)
        clean_nim_define_btn    = Button(third_row, text="%d:" % (CLEANNIMRESOURCE + 1) + CMDMsg.getCmdDesc(CLEANNIMRESOURCE),
                                         width=widget_width, height=widget_height)
        accept_license_btn      = Button(third_row, text="%d:" % (ACCEPTLICENSE + 1) + CMDMsg.getCmdDesc(ACCEPTLICENSE),
                                         width=widget_width, height=widget_height)
        power_off_svr_btn       = Button(third_row, text="%d:" % (POWEROFFSERVER + 1) + CMDMsg.getCmdDesc(POWEROFFSERVER),
                                         width=widget_width, height=widget_height)
        remv_vios_from_hmc_btn  = Button(third_row, text="%d:" % (REMVSERVER + 1) + CMDMsg.getCmdDesc(REMVSERVER),
                                         width=widget_width, height=widget_height)
        hmc2ivm_reset_fw_fctry_btn \
                                = Button(third_row, text="%d:" % (RST_FW_FCTRY + 1) + CMDMsg.getCmdDesc(RST_FW_FCTRY),
                                         width=widget_width, height=widget_height)

        remv_connection_btn     = Button(fourth_row, text="%d:" % (RMV_NON_HMC + 1) + CMDMsg.getCmdDesc(RMV_NON_HMC),
                                         width=widget_width, height=widget_height)
        asm_poweron_btn         = Button(fourth_row, text="%d:" % (ASM_POWERON + 1) + CMDMsg.getCmdDesc(ASM_POWERON),
                                         width=widget_width, height=widget_height)

        installPd_btn           = Button(fourth_row, text="%d:" % (INSTALLSW + 1) + CMDMsg.getCmdDesc(INSTALLSW),
                                         width=widget_width, height=widget_height)
        set_default_ip_btn      = Button(fourth_row, text="%d:" % (SET_DEFAULT_IP + 1) + CMDMsg.getCmdDesc(SET_DEFAULT_IP),
                                         width=widget_width, height=widget_height)      
        showRecords_btn         = Button(fourth_row, text="%d:" % (SHOWRECORDS + 1) + CMDMsg.getCmdDesc(SHOWRECORDS),
                                         width=widget_width, height=widget_height)
#         save_selections_btn     = Button(fourth_row, text="%d:" % (SAVESELECTION + 1) + CMDMsg.getCmdDesc(SAVESELECTION),
#                                          width=widget_width, height=widget_height)
#         hello_btn               = Button(self, text="Hello", 
#                                          width="30", height=widget_height)
#         

        
        first_row.pack(side=TOP)
        #auto_btn.pack(side=LEFT)
        #manual_btn.pack(side=RIGHT)
        ipscan_btn.pack(side=LEFT)
        update_passwd_btn.pack(side=LEFT)
        recover_profile_btn.pack(side=LEFT)
        power_on_svr_btn.pack(side=LEFT)
        
        second_row.pack(side=TOP)
        create_vios_lpar_btn.pack(side=LEFT)
        prepare_hosts_file_btn.pack(side=LEFT)
        define_nim_host_btn.pack(side=LEFT)
        allocate_sources_btn.pack(side=LEFT)
        install_vios_btn.pack(side=LEFT)
        clean_nim_define_btn.pack(side=LEFT)
        accept_license_btn.pack(side=LEFT)
        
        third_row.pack(side=TOP)
        power_off_svr_btn.pack(side=LEFT)
        remv_vios_from_hmc_btn.pack(side=LEFT)
        hmc2ivm_reset_fw_fctry_btn.pack(side=LEFT)
        #hmc2ivm_btn.pack(side=TOP)
        remv_connection_btn.pack(side=LEFT)
        asm_poweron_btn.pack(side=LEFT)
        
        fourth_row.pack(side=TOP)
        installPd_btn.pack(side=LEFT)
#        get_status_btn.pack(side=LEFT)
        set_default_ip_btn.pack(side=LEFT)
        showRecords_btn.pack(side=LEFT)
        
        #self.cntl_btns.append(update_passwd_btn)
        self.cntl_btns.append(showRecords_btn)
        self.cntl_btns_panel.append(first_row)
        self.cntl_btns_panel.append(second_row)
        self.cntl_btns_panel.append(third_row)
        self.cntl_btns_panel.append(fourth_row)
        

#        save_selections_btn.pack(side=LEFT)
#        hello_btn.pack()
        
#         state_buttons = [update_passwd_btn, recover_profile_btn, 
#                          power_on_svr_btn, create_vios_lpar_btn, prepare_hosts_file_btn, 
#                          define_nim_host_btn, allocate_sources_btn, install_vios_btn,
#                          power_off_svr_btn, remv_connection_btn, remv_vios_from_hmc_btn,
#                          hmc2ivm_reset_fw_fctry_btn, 
#                          ]
#         state_idx = 2
#         for btn in state_buttons:
#             btn.config(command=lambda idx=state_idx: self.launch_state_task(idx))
#             state_idx += 1

        #expnd_clps_btn.config(command=self.showhidebtns)
        ipscan_btn.config(command=self.server_scan)
        update_passwd_btn.config(command=lambda idx=UPDATEPASSWD_STAT: self.launch_state_task(idx))
        recover_profile_btn.config(command=lambda idx=RECOVERPROFILE_STAT: self.launch_state_task(idx))
        power_on_svr_btn.config(command=lambda idx=POWERONSERVER_STAT: self.launch_state_task(idx))
        
        create_vios_lpar_btn.config(command=lambda idx=CREATEVIOSLPAR_STAT: self.launch_state_task(idx))
        prepare_hosts_file_btn.config(command=lambda idx=PREPAREHOSTSFILE_STAT: self.launch_state_task(idx))
        define_nim_host_btn.config(command=lambda idx=DEFINESERVER_STAT: self.launch_state_task(idx))
        allocate_sources_btn.config(command=lambda idx=ASSIGNRESOURCE_STAT: self.launch_state_task(idx))
        install_vios_btn.config(command=lambda idx=INSTALL_VIOS_STAT: self.launch_state_task(idx))
        clean_nim_define_btn.config(command=lambda idx=CLEAN_NIM_RESOURCE_STAT: self.launch_state_task(idx))
        accept_license_btn.config(command=lambda idx=ACCEPTLICENSE_STAT: self.launch_state_task(idx))

        power_off_svr_btn.config(command=lambda idx=POWEROFFSERVER_STAT: self.launch_state_task(idx))
        remv_vios_from_hmc_btn.config(command=lambda idx=REMVSERVER_STAT: self.launch_state_task(idx))
        hmc2ivm_reset_fw_fctry_btn.config(command=lambda idx=RST_FW_FCTRY_STAT: self.launch_state_task(idx))
        remv_connection_btn.config(command=lambda idx=RMV_NON_HMC_STAT: self.launch_state_task(idx))
        asm_poweron_btn.config(command=lambda idx=ASM_POWERON_STAT: self.launch_state_task(idx))
        installPd_btn.config(command=lambda idx=INSTALLSW_STAT: self.launch_state_task(idx))
        set_default_ip_btn.config(command=lambda idx=SET_DEFAULT_IP_STAT: self.launch_state_task(idx))
#        get_status_btn.config(command=self.get_current_status)
        showRecords_btn.config(command=self.showhidePanel)
        
#        hello_btn.config(command=self.hello_test)

    def __init__(self, parent, appl, controller):
        '''
        Constructor
        '''
        DebugLog.info_print("Construct Control Buttons Panel")
        self.cntl_btns_visible = False
        self.cntl_btns = []
        self.cntl_btns_panel = []
        BasePanel.__init__(self, parent, appl, controller)
        
        self.msg_coder = MsgCodec()

        
    
    



        
        