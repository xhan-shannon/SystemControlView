# -*- coding: utf-8 -*-
'''
Created on 2015��1��13��

@author: stm
'''


import time
from remote_session import Remote_Session
from utils import DebugLog
from utils.IPCheck import IPCheck


class HMC_CLI(object):
    '''
    The class maintains the HMC Command line interface connection
    which uses ssh session
    '''

    def __init__(self, target, password, with_config=True):
        '''
        connectSSH the target
        Use pexpect to implement the ssh connection;
        Would replace it with paramiko module
        '''
        self.target = target
        self.password = password
        username = 'hscroot'

        self.remote_session = Remote_Session(target, username, password)
        
    
    def add_managed_system(self, ip):
        '''add a system as managed node'''
        # self.remote_session.interactive_cmds(cmd, expect_prompt, with_return)
        DebugLog.info_print("create managed system connection")
        self.make_sys_connection(ip)

        success = False
        for count in range(10):
            time.sleep(5)
            status = self.get_sys_conns(ip)
            status = status.split(',')
            DebugLog.info_print(str(status))
            DebugLog.info_print(status[-1])
            if "Connected" == status[-1]:
                DebugLog.info_print("success to add the system: %s into hmc" % ip)
                success = True
                break

        if not success:
            DebugLog.info_print("failed to add the system: %s into hmc" % ip)


    def get_sys_conns(self, ip):
        '''Get sys connection list
           The format is : ip,state
                    eg: 172.30.126.3,Connected
        '''
        conns_list = self.remote_session.get_sys_conn()
        DebugLog.info_print("Get the sys connections: " + str(conns_list))
        idx = 0
        for idx in range(len(conns_list)):
            if ip in conns_list[idx]:
                DebugLog.info_print("Got the connection for ip %s" % ip)
                DebugLog.info_print(conns_list[idx])
                return conns_list[idx]
        DebugLog.info_print("Not Got the connection for ip %s" % ip)

        
        
    def remove_hmc_connection(self, ip):
        '''To remove the hmc connection'''
        cmd = "rmsysconn --ip %s -o remove" % ip
        DebugLog.info_print("remove the desired server %s from hmc" % ip)
        self.remote_session.interactive_cmds(cmd, "~>  ~>", False)
        

    def poweroff_server(self, server_name):
        '''To remove the hmc connection'''
        cmd = "chsysstate -m %s -o off -r sys " % server_name
        DebugLog.info_print("poweroff the desired server %s " % server_name)
        self.remote_session.interactive_cmds(cmd, "~>  ~>", False)
 

    def poweron_server(self, server_name):
        '''To remove the hmc connection'''
        cmd = "chsysstate -m %s -o onstandby -r sys " % server_name
        DebugLog.info_print("poweron the designated server %s " % server_name)
        self.remote_session.interactive_cmds(cmd, "~>  ~>", False)
                                             
                                             
    def make_sys_connection(self, ip):
        '''create system connection'''
        self.remote_session.create_sys_conn(ip)

    
    def make_sys_connection_auto(self):
        '''create system connection'''
        cmd = "mksysconn -o auto"
        self.remote_session.interactive_cmds(cmd, "~>  ~>", False)
        
    
    
    def get_managed_sys_info(self):
        '''
        get the managed system connection
        scan and get the ip and serial_num
        '''
        cmd = "lssyscfg -r sys -F name,ipaddr,serial_num,state"
        scan_results = self.remote_session.interactive_cmds(cmd, "~>  ~>", True)
        return scan_results
    
    def get_server_status(self, mserver):
        '''get the specific server status'''
        cmd = "lssyscfg -r sys -m %s -F state" % mserver
        status_results = self.remote_session.interactive_cmds(cmd, "~>  ~>", True)
        return status_results
    
    
    def server_scan(self):
        '''
        connect hmc as a session 
        issue the command:
        return: IP,SN,Status 
        '''
        DebugLog.info_print("scan the dhcp client ip and the respective sn")
        self.make_sys_connection_auto()
        results = self.get_managed_sys_info()
        return results
    
    
    def get_current_status(self, server_name):
        '''
        Get the current server status
        '''
        cmd = "lssyscfg -r sys -m %s -F name,state" % server_name
        server_status = self.remote_session.interactive_cmds(cmd, "~>  ~>", True)
        return server_status
    
    
    def get_server_name(self,managed_sys_name):
        DebugLog.info_print("get the server name desired machine %s " % managed_sys_name)
        cmd = "lssyscfg -r sys -F name,ipaddr |grep %s | cut -d ',' -f 1" % managed_sys_name 
        server_name = self.remote_session.interactive_cmds(cmd, "~>  ~>", True)[0]
        DebugLog.info_print(server_name)
        return server_name 
    

    def get_server_name_by_sn(self, serial_num):
        DebugLog.info_print("get the server name desired machine %s " % serial_num)
        cmd = "lssyscfg -r sys -F name,serial_num |grep %s | cut -d ',' -f 1" % serial_num 
        server_name = self.remote_session.interactive_cmds(cmd, "~>  ~>", True)[0]
        DebugLog.info_print(server_name)
        return server_name 
    
            
    def update_password(self, machine_name):
        '''
        update the password for the desired machine 
        '''
        DebugLog.info_print("update the password for the desired machine %s " % machine_name)
        resp = self._change_sys_pwd(machine_name)
        DebugLog.info_print("response: %s" % resp)
 

    def _change_sys_pwd(self, managed_sys_name):
        '''Changes a password for a managed system or a managed frame.'''
        result_log = []
        
        result_item1 = []
        cmd = 'chsyspwd -m %s -t access --passwd admin --newpasswd admin' \
                % managed_sys_name
        result_item1.append(cmd)
        result = self.remote_session.interactive_cmds(cmd, "~>  ~>", True)
        result_item1.append(result)
        failed_expected_ret = "The old password specified for the user was incorrect. Try the operation again."
        go_to_next = False
        if failed_expected_ret in result:
            go_to_next = True
        result_log.append(result_item1)
        
        server_name = self.get_server_name(managed_sys_name)
        if not go_to_next:
            is_ip_fromat = IPCheck.ip_format_check(server_name)
            #while server_name == managed_sys_name:
            count = 0
            while is_ip_fromat:
                if count > 10:
                    self._change_sys_pwd(server_name)
                    return
                count += 1
                time.sleep(2)
                server_name = self.get_server_name(managed_sys_name)
                is_ip_fromat = IPCheck.ip_format_check(server_name)
            
        result_item2 = []
        cmd = 'chsyspwd -m %s -t admin --passwd admin --newpasswd admin' \
                % server_name
        DebugLog.info_print(cmd)
        result_item2.append(cmd)
        result = self.remote_session.interactive_cmds(cmd, "~>  ~>", True)
        result_item2.append(result)
        result_log.append(result_item2)
        DebugLog.info_print(cmd)
        
        
        time.sleep(1)
        result_item3 = []
        cmd = 'chsyspwd -m %s -t general --passwd general --newpasswd general' \
                % server_name
        
        result_item3.append(cmd)
        result = self.remote_session.interactive_cmds(cmd, "~>  ~>", True)
        result_item3.append(result)
        result_log.append(result_item3)

        
        return result_log
                
    
    def get_os_name(self):
        '''return the os name'''
        return self.remote_session.cmd_output("uname")


    def goto_super_mode(self):
        '''go into super mode'''
        self.remote_session.interactive_cmd_output("su - padmin")


    def exit_super_mode(self):
        '''exit the super mode'''
        self.remote_session.interactive_cmd_output("exit")


    def get_pwd_result(self):
        '''return pwd result'''
        return self.remote_session.interactive_cmd_output("pwd")

    def get_sys_conn(self):
        '''return sys connection'''
        # self.goto_super_mode()
        sys_conns = self.remote_session.interactive_cmds("lssysconn -r all -F ipaddr,state",
                                                         "~>  ~>",
                                                         True)
        # version = self.cmd_output("oslevel")
        # self.get_pwd_result()
        # self.exit_super_mode()

        return sys_conns


    def create_sys_conn(self, ip):
        '''create system connection'''
        cmd = "mksysconn --ip %s -r sys --passwd admin" % ip
        self.remote_session.interactive_cmds(cmd, "~>  ~>", False)


    def recover_profile(self, server_name):
        '''recover profile for a server which specified by server name'''
        cmd = "rstprofdata -m  %s -l 4" % server_name
        DebugLog.info_print("recover profile %s " % server_name)
        self.remote_session.interactive_cmds(cmd, "~>  ~>", False)
        
    
    def get_server_slots(self, server_name):
        '''get slots info from hmc'''
        cmd = "lshwres -r io --rsubtype slot -m %s -F drc_index" % server_name
        DebugLog.info_print("get slots %s " % server_name)
        server_slots = self.remote_session.interactive_cmds(cmd, "~>  ~>", True)
        
        return server_slots
    
    def check_if_create_vios_lpar_finished(self, server_name, server_sn):
        '''To check if the specified server_sn on server is created
           @server_name: 
           @server_sn
           $create_vios_finish: if created, return True
        '''
        create_vios_finish = False
        chk_lpar_cmd = 'lssyscfg -r lpar -m %s -F name' % server_name
        chk_lpar_result = self.remote_session.interactive_cmds(chk_lpar_cmd, "~>  ~>", True)
        if server_sn in chk_lpar_result:
            create_vios_finish = True
            
        return create_vios_finish
            
        
    def get_lpar_id(self, server_name, server_sn):
        '''
        Get lpar id
        '''
        chk_lpar_cmd = 'lssyscfg -r lpar -m %s -F state,lpar_id --filter lpar_names=%s' % (server_name, server_sn)
        chk_lpar_result = self.remote_session.interactive_cmds(chk_lpar_cmd, "~>  ~>", True)
        chk_lpar_result = chk_lpar_result[0].split(',')
        DebugLog.info_print(str(chk_lpar_result))
        
        return chk_lpar_result[1]
    
        
    def test_if_lpar_existed(self, server_name, server_sn):
        '''
        Test if a lpar with the specified name existed
        '''
        bexisted = False
        chk_lpar_cmd = 'lssyscfg -r lpar -m %s -F state,lpar_id --filter lpar_names=%s' % (server_name, server_sn)
        chk_lpar_result = self.remote_session.interactive_cmds(chk_lpar_cmd, "~>  ~>", True)
        chk_lpar_result = chk_lpar_result[0].split(',')
        DebugLog.info_print(str(chk_lpar_result))
        
        if 2 == len(chk_lpar_result):
            bexisted = True
            
        return bexisted
    
        
    def remove_lpar(self, server_name, lpar_id):  
        '''
        remove a not activated lpar
        '''          
        rmlparcmd='rmsyscfg -r lpar -m %s --id %s' % (server_name, lpar_id)
        self.remote_session.interactive_cmds(rmlparcmd, "~>  ~>", False)
        
        
    def test_if_lpar_notactived(self, server_name, server_sn):
        '''
        Test if a lpar with the specified name not activated
        '''
        bActived = False
        chk_lpar_cmd = 'lssyscfg -r lpar -m %s -F state,lpar_id --filter lpar_names=%s' % (server_name, server_sn)
        chk_lpar_result = self.remote_session.interactive_cmds(chk_lpar_cmd, "~>  ~>", True)
        chk_lpar_result = chk_lpar_result[0].split(',')
        DebugLog.info_print(str(chk_lpar_result))
        
        if 'Not Activated' == chk_lpar_result[0]:
            bActived = True
            
        return bActived
    
    
    def shutdown_lpar(self, server_name, lpar_id):
        '''
        Shutdown lpar
        '''
        shutdowncmd='chsysstate -m %s -o shutdown -r lpar --immed --id %s' % (server_name, lpar_id)
        self.remote_session.interactive_cmds(shutdowncmd, "~>  ~>", False)
                
                
    def chk_and_shutdown_remv_lpar(self, server_name, server_sn):
        '''
        check if the lpar already existed, then shutdown it and remove it
        '''

        if self.test_if_lpar_existed(server_name, server_sn):
            # there is already a lpar existed
            _lpar_id = self.get_lpar_id(server_name, server_sn)
            self.shutdown_lpar(server_name, _lpar_id)
            
            while not self.test_if_lpar_notactived(server_name, server_sn):
                time.sleep(3)
                
            self.remove_lpar(server_name, _lpar_id)
            
            while self.test_if_lpar_existed(server_name, server_sn):
                time.sleep(1)
                
            
 
    
    
    def create_vios_lpar(self, params_list):
        '''create vios lpar'''
        
        params = params_list
        if not isinstance(params_list, list):
            params = eval(params_list)
        server_name, server_sn, server_slots = params
        _name = server_sn
        _profile_name = '%sprf' % server_sn 
        self.chk_and_shutdown_remv_lpar(server_name, server_sn)
        time.sleep(1)
        cmd = 'mksyscfg -r lpar -m %s -i "name=%s,\
               profile_name=%s,lpar_env=vioserver,auto_start=1,\
               boot_mode=norm,mem_mode=ded,min_mem=2048,\
               desired_mem=4096,max_mem=8192,\
               proc_mode=shared,min_procs=2,desired_procs=4,\
               max_procs=8,min_proc_units=0.5,desired_proc_units=1,\
               max_proc_units=2,\
               sharing_mode=cap,max_virtual_slots=200,\
               \\"io_slots=%s//0\\""' % (server_name, 
                                     _name, 
                                     _profile_name,
                                     server_slots) 
        DebugLog.info_print("create vios lpar for %s " % server_name)
        self.remote_session.interactive_cmds(cmd, "~>  ~>", False)
        
    
    def lpar_net_boot(self, data):
        '''install vios'''
        assert(isinstance(data, dict))
        _name_server_ip = data['name_server_ip']
        _gateway = data['gateway']
        _client_ip = data['client_ip']
        _server_sn = data['server_sn']
        _server_prf = data['server_prf']
        _server_name = data['server_name']
     
        _lpar_mac = self.get_lpar_mac(_server_name, _server_sn)
        #lpar_netboot -f -t ent -m 6cae8b687df4 
#                       -T off -s auto -d auto 
#                       -S 192.168.9.1 
#                       -G 192.168.9.1 
#                       -C 192.168.9.10 
#                       060A17A 
#                       060A17Aprf 
#                       Server-8246-L1T-SN060A17A
                      
        cmd = 'lpar_netboot -f -t ent -T off -s auto -d auto \
               -m %s \
               -S %s \
               -G %s \
               -C %s \
               %s \
               %s \
               %s' % (_lpar_mac,
                      _name_server_ip, 
                      _gateway, 
                      _client_ip,
                      _server_sn, 
                      _server_prf,
                      _server_name)

        DebugLog.debug_print_level1("install vios for %s " % _server_name)
        DebugLog.debug_print_level1("cmd: %s" % cmd)
        ret_val = self.remote_session.interactive_cmds(cmd, "~>  ~>", True)
        DebugLog.debug_print_level1("return value: %s " % ret_val)
        
        
    def get_lpar_mac(self, server_name, server_sn):
        '''
        Get lpar mac address
        '''
        _server_prf = "%sprf" %  server_sn
        get_lpar_mac_cmd = "lpar_netboot -M -n -t ent %s %s %s" % (server_sn, _server_prf, server_name)
        retresult = self.remote_session.interactive_cmds(get_lpar_mac_cmd, "~>  ~>", True)
        mac_val_ret = retresult[-1]
        mac = mac_val_ret.split()[2]
        
        return mac

    
    def get_server_status_and_name(self, _server_name):
        '''get the specific server status'''
        cmd = "lssyscfg -r sys -m %s -F state,name" % _server_name
        status_results = self.remote_session.interactive_cmds(cmd, "~>  ~>", True)
        return status_results
    
    

        