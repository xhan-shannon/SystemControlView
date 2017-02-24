#--*-- coding:utf-8 --*--
'''
Created on 2015��6��8��

@author: stm
'''

import telnetlib

from base.engine import EngineBase
from utils import DebugLog
from base.cmdmsg import CHECKVIOSINSTALL, CMDMsg, INSTALLVIOS, ACCEPTLICENSE,\
    CHECKACCEPTLICENSE, CHECKASM_POWERON, ASM_POWERON, SET_DEFAULT_IP, INSTALLSW,\
    SET_DEFAULT_IP_AND_SHUTDOWN
from base.vdstate import PRGRS_FINISHED, INSTALL_VIOS_STAT, PRGRS_INPROGRESS,\
    StateBase, UPDATEPASSWD_STAT, ACCEPTLICENSE_STAT, ASM_POWERON_STAT,\
    SET_DEFAULT_IP_STAT, INSTALLSW_STAT, SET_DEFAULT_IP_AND_SHUTDOWN_STAT
import time
from engine.sessions.servercli_session import Server_CLI
import os
from multiprocessing.process import Process




CRRT = '\r\n'

class ServerEng(EngineBase):
    '''
    Test the designed server method
    '''


    def __init__(self, vd_comm_cnt, vd_config):
        '''
        Constructor
        '''
        DebugLog.info_print("ServerEng initialized")
        EngineBase.__init__(self, vd_comm_cnt, vd_config)

        self.ip = ""
        self.vd_config = vd_config
        try:
            self.root_user_passwd = self.vd_config.get('server_config', 'rootuser_passwd')
            self.sw_type          = self.vd_config.get('server_config', 'sw_type')
            self.sw_dir           = self.vd_config.get('software_dist', "directory")
            self.sw_version       = self.vd_config.get('software_dist', "version")
        except:
            self.root_user_passwd = "teamsun"
        
    
    #@staticmethod
    def test_if_accessable(self, server_id, ip):
        baccess = False
        ret = ""
        serverip = eval(ip)
        _server_ip = serverip[0]
        
        try:
            tn = telnetlib.Telnet(_server_ip)
            ret = tn.read_until("login: ", 5)
        except Exception, e:
            if isinstance(e, EOFError):
                ret = None
        
        if ret:
            baccess = True
        
        if baccess:
            resp_msg = EngineBase.get_post_phase_progress_msg(server_id, 
                                           INSTALL_VIOS_STAT, 
                                           PRGRS_FINISHED, 
                                           INSTALLVIOS)           
        else:
            resp_msg = EngineBase.get_post_phase_progress_msg(server_id, 
                                           INSTALL_VIOS_STAT, 
                                           PRGRS_INPROGRESS, 
                                           INSTALLVIOS)
        if resp_msg:
            time.sleep(5)
            self.vd_comm_cnt.postMessage(resp_msg)
            
            
    def check_if_asm_power_on(self, server_id, ip):
        baccess = False
        ret = ""
        serverip = eval(ip)
        _server_ip = serverip[0]
        
        try:
            tn = telnetlib.Telnet(host=_server_ip,port=22)
            ret = tn.read_until("SSH-", 5)
        except Exception, e:
            if isinstance(e, EOFError):
                ret = None
        
        if ret:
            baccess = True
        
        if baccess:
            resp_msg = EngineBase.get_post_phase_progress_msg(server_id, 
                                           ASM_POWERON_STAT, 
                                           PRGRS_FINISHED, 
                                           ASM_POWERON)           
        else:
            resp_msg = EngineBase.get_post_phase_progress_msg(server_id, 
                                           ASM_POWERON_STAT, 
                                           PRGRS_INPROGRESS, 
                                           ASM_POWERON)
        if resp_msg:
            self.vd_comm_cnt.postMessage(resp_msg)
                
      
    def modify_padmin_passwd(self, server_id, data):
        '''
        modify padmin password
        '''
        bFinished = False
        change_passwd_sign = "padmin's New password:"
        login_passwd_sign = "padmin's Password:"
        accept_license_sign = "Accept (a) |  Decline (d) |  View Terms (v)"
        shell_prompt_sign = "$"
        rootuser_prompt_sign = "#"
        
        _ip = eval(data)
        ip = _ip[0]
        try:
            tn = telnetlib.Telnet(ip)
            ret = ""
            ret = tn.read_until("login: ", 5)
            DebugLog.info_print("print accept license1")
            
            if ret:
                tn.write("padmin" + CRRT)               
                read_cont = tn.read_until("padmin's New password:", 10)
                DebugLog.info_print("print accept license2")
                
                read_cont = read_cont.strip()
                if read_cont.endswith(change_passwd_sign):
                    tn.write("padmin" + CRRT)
                    ret_exp = tn.read_until("Enter the new password again:", 10)
                    DebugLog.info_print("print accept license3")
                    if ret_exp:
                        tn.write("padmin" + CRRT)                        
                        read_cont = tn.read_until(accept_license_sign, 10)
                        DebugLog.info_print("print accept license4")
                        
                        if accept_license_sign in read_cont:
                            tn.write("a" + CRRT)
                            read_cont = tn.read_until(shell_prompt_sign)
                            DebugLog.info_print("print accept license5")
                            bFinished = True
        except Exception:
            bFinished = False
            
        return bFinished
            
            
    def accept_license_and_enable_root_user(self, server_id, data):
        '''
        Capture login: prompt, then input padmin as password
        license accept
        '''
        bFinished = False
        change_passwd_sign = "padmin's New password:"
        login_passwd_sign = "padmin's Password:"
        accept_license_sign = "Accept (a) |  Decline (d) |  View Terms (v)"
        enter_passwd_again = "Enter the new password again:"
        shell_prompt_sign = "$"
        rootuser_prompt_sign = "#"
        
        _ip = eval(data)
        ip = _ip[0]
        try:
            tn = telnetlib.Telnet(ip)
            ret = ""

            ret = tn.read_until("login: ", 5)
            DebugLog.info_print("%s: %s [%s]" % (ip, ret, "accept_license_and_enable_root_user"))
            
            if ret:
                tn.write("padmin\r\n")
                
                read_cont = tn.read_until("padmin's New password:", 5)
                DebugLog.info_print("%s: %s [%s]" % (ip, read_cont, "accept_license_and_enable_root_user"))
                
                read_cont = read_cont.strip()
                if read_cont.endswith(change_passwd_sign):
                    tn.write("padmin" + CRRT)
                    ret_exp = tn.read_until("Enter the new password again:", 5)
                    DebugLog.info_print("%s: %s [%s]" % (ip, ret_exp, "accept_license_and_enable_root_user"))
                    if ret_exp:
                        tn.write("padmin" + CRRT)
                elif read_cont.endswith(login_passwd_sign):
                    tn.write("padmin" + CRRT)
                    read_cont = tn.read_until(accept_license_sign, 5)
                    DebugLog.info_print("%s: %s [%s]" % (ip, read_cont, "accept_license_and_enable_root_user"))
                    
                    if accept_license_sign in read_cont:
                        tn.write("a" + CRRT)
                        read_cont = tn.read_until(shell_prompt_sign)
                        DebugLog.info_print("%s: %s [%s]" % (ip, read_cont, "accept_license_and_enable_root_user"))
                    elif read_cont.strip().endswith(shell_prompt_sign):
                        tn.write("license -accept" + CRRT)
                        read_cont = tn.read_until(shell_prompt_sign, 5)
                        DebugLog.info_print("%s: %s [%s]" % (ip, read_cont, "accept_license_and_enable_root_user"))
                        
                        # to enter oem_setup_env mode
                        if read_cont.strip().endswith(shell_prompt_sign):
                            tn.write("oem_setup_env" + CRRT)
                            read_cont = tn.read_until(rootuser_prompt_sign, 5)
                            DebugLog.info_print("%s: %s [%s]" % (ip, read_cont, "accept_license_and_enable_root_user"))
                            # change password
                            tn.write("passwd" + CRRT)
                            read_cont = tn.read_until("assword:", 10)
                            DebugLog.info_print("%s: %s [%s]" % (ip, read_cont, "accept_license_and_enable_root_user"))
                            tn.write(self.root_user_passwd + CRRT)
                            read_cont = tn.read_until(enter_passwd_again, 5)
                            DebugLog.info_print("%s: %s [%s]" % (ip, read_cont, "accept_license_and_enable_root_user"))
                            tn.write(self.root_user_passwd + CRRT)
                            read_cont = tn.read_until(rootuser_prompt_sign, 5)
                            DebugLog.info_print("%s: %s [%s]" % (ip, read_cont, "accept_license_and_enable_root_user"))
                            
                            # enable root su login from console
#                            tn.write("chuser login=true root \r\n")
#                            tn.write(" chusersu=true root \r\n")
#                            tn.write("cp -p /usr/bin/su /home/padmin \r\n")
                            
                            bFinished = True
                 
        except Exception:
            bFinished = False
        
        return bFinished

        
    def modify_passwd_and_accept_license(self, _server_id, data):
        '''
        Capture login: prompt, then input padmin as password
        license accept
        '''
        DebugLog.debug_print_level1("Connect hmc client session, update_password")
        resp_state = [StateBase.get_state_const(ACCEPTLICENSE_STAT), 
                      StateBase.get_state_progress_const_name(PRGRS_INPROGRESS)]
        
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(ACCEPTLICENSE),
                                         _server_id, 
                                         resp_state)
        
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
        
        bFinished = False
        
        self.modify_padmin_passwd(_server_id, data)
        bFinished = self.accept_license_and_enable_root_user(_server_id, data)
        return bFinished

    
    
    def check_license_accepted_and_rootuser_enabled(self, _server_id, data):
        '''
        check license if accepted and test whether the root role command
        '''
        '''
        Capture login: prompt, then input padmin as password
        license accept
        '''
        bFinished = False
        
        _ip = eval(data)
        ip = _ip[0]
        change_passwd_sign = "padmin's New password:"
        login_passwd_sign = "padmin's Password:"
        accept_license_sign = "Accept (a) |  Decline (d) |  View Terms (v)"
        shell_prompt_sign = "$"
        rootuser_prompt_sign = "#"
        
        try:
            tn = telnetlib.Telnet(ip)
            ret = ""

            ret = tn.read_until("login: ", 5)
            DebugLog.info_print("print accept license6")
            
            if ret:
                tn.write("padmin\r\n")
                
                read_cont = tn.read_until("padmin's New password:", 10)
                DebugLog.info_print("print accept license7")
                
                read_cont = read_cont.strip()
                if read_cont.endswith(login_passwd_sign):
                    tn.write("padmin\r\n")
                    read_cont = tn.read_until(shell_prompt_sign, 10)
                    
                    if read_cont.strip().endswith(shell_prompt_sign):
                        tn.write("ls -l \r\n")
                        read_cont = tn.read_until(shell_prompt_sign, 10)
                        
                        if read_cont.strip().endswith(shell_prompt_sign):           
                            bFinished = True
                 
        except Exception:
            bFinished = False
        
        if bFinished:
            try:
                tn = telnetlib.Telnet(host=ip, port=22)
                ret = tn.read_until("SSH-", 10)
            except Exception, e:
                if isinstance(e, EOFError):
                    ret = None
                    
            if not ret:
                bFinished = False
                
        
        if bFinished:
            resp_msg = EngineBase.get_post_phase_progress_msg(_server_id, 
                                           ACCEPTLICENSE_STAT, 
                                           PRGRS_FINISHED, 
                                           ACCEPTLICENSE)           
        else:
            resp_msg = EngineBase.get_post_phase_progress_msg(_server_id, 
                                           ACCEPTLICENSE_STAT, 
                                           PRGRS_INPROGRESS, 
                                           ACCEPTLICENSE)
        if resp_msg:
            self.vd_comm_cnt.postMessage(resp_msg)
    
    
    def install_software(self, server_id, server_ip):
        '''install software'''
        def _system_call(svr_ip):
            cmd_name = "./utils/Puppet/client.pyo"
            #params = " -i -2.5 target_ip passwrod version_number"
            self.sw_version = "2.5.4.37"
            exec_cmd = "python -O %s -i -2.5 %s %s %s" % \
                    (cmd_name, svr_ip, self.root_user_passwd, self.sw_version)
            DebugLog.info_print(exec_cmd)
            cur_work_dir = os.getcwd()
            DebugLog.info_print(cur_work_dir)
            os.system(exec_cmd)
                    
        resp_state = [StateBase.get_state_const(INSTALLSW_STAT), 
                      StateBase.get_state_progress_const_name(PRGRS_INPROGRESS)]
 
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(INSTALLSW),
                                         server_id, 
                                         resp_state)
             
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
                       
        svrip = eval(server_ip)
        _server_ip = svrip[0]
        
        #_server_ip = "192.168.9.22"
#         p = Process(target=_system_call, args=(_server_ip,))
#         p.start()
#         p.join()
            
        
        _system_call(_server_ip)
        resp_state = [StateBase.get_state_const(INSTALLSW_STAT), 
                      StateBase.get_state_progress_const_name(PRGRS_FINISHED)]

        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(INSTALLSW),
                                         server_id, 
                                         resp_state)
            
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
        
    
    def set_default_ip(self, server_id, data, bshutdown=False):
        '''set default ip as 192.168.9.188'''
        
        phase_idx = SET_DEFAULT_IP_STAT
        cmd_idx = SET_DEFAULT_IP
        if bshutdown:
            phase_idx = SET_DEFAULT_IP_AND_SHUTDOWN_STAT
            cmd_idx = SET_DEFAULT_IP_AND_SHUTDOWN
            
        resp_state = [StateBase.get_state_const(phase_idx), 
                      StateBase.get_state_progress_const_name(PRGRS_INPROGRESS)]
 
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(cmd_idx),
                                         server_id, 
                                         resp_state)
             
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
         
        _server_sn, _server_ip = eval(data)
        
        server_cli = None
        count_connect = 0
        
        while not server_cli and count_connect < 100:
            try:
                server_cli = Server_CLI(_server_ip, self.root_user_passwd)
                break
            except:
                server_cli = None
                count_connect += 1
                DebugLog.info_print("Server ssh connect failed count: %d" % count_connect)
                time.sleep(2)
                
            
        server_cli.set_default_ip_and_shutdown(_server_sn, bshutdown)
        
        resp_state = [StateBase.get_state_const(phase_idx), 
                      StateBase.get_state_progress_const_name(PRGRS_FINISHED)]
 
        msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(cmd_idx),
                                         server_id, 
                                         resp_state)
             
        DebugLog.debug_print_level1(msg)
        self.vd_comm_cnt.postMessage(msg)
        
        
    
    def check_installed_software(self):
        '''check if the installation finished succesfully'''
        pass
        
        
        
        
    def process_message(self, msg):
        DebugLog.debug_print_level1("Got the command tranfering in server engine")
        cmd, _server_id, data = self.msg_decoder.decodeMsg(msg)
        if CMDMsg.getCMD(CHECKVIOSINSTALL) == cmd:
            self.test_if_accessable(_server_id, data)
        elif CMDMsg.getCMD(ACCEPTLICENSE) == cmd:
            ret = self.modify_passwd_and_accept_license(_server_id, data)
            # Do it twice to make sure accept license is finished
            if not ret:
                self.modify_passwd_and_accept_license(_server_id, data)
        elif CMDMsg.getCMD(CHECKACCEPTLICENSE) == cmd:
            self.check_license_accepted_and_rootuser_enabled(_server_id, data)
        elif CMDMsg.getCMD(CHECKASM_POWERON) == cmd:
            self.check_if_asm_power_on(_server_id, data)
        elif CMDMsg.getCMD(INSTALLSW) == cmd:
            self.install_software(_server_id, data)
        elif CMDMsg.getCMD(SET_DEFAULT_IP) == cmd:
            self.set_default_ip(_server_id, data)
        elif CMDMsg.getCMD(SET_DEFAULT_IP_AND_SHUTDOWN) == cmd:
            self.set_default_ip(_server_id, data, bshutdown=True)
        