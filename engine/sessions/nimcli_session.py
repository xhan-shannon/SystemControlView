# -*- coding: utf-8 -*-
'''
Created on 2015锟斤拷1锟斤拷13锟斤拷

@author: stm
'''


import time
from remote_session import Remote_Session
from utils import DebugLog


class NIM_CLI(object):
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
        username = "root"

        self.remote_session = Remote_Session(target, username, password)
        

    def remove_allocated_resource_in_nim(self, server_sn):
        '''reset, deallocate and remove the allocated resource in nim server'''
        reset_cmd = "nim -o reset -F %s" % server_sn
        self.remote_session.interactive_cmds(reset_cmd, "#  #", False)
        dealloc_cmd = "nim -o deallocate -a subclass=all %s" % server_sn
        self.remote_session.interactive_cmds(dealloc_cmd, "#  #", False)
        remove_cmd = "nim -o remove %s" % server_sn
        self.remote_session.interactive_cmds(remove_cmd, "#  #", False)
        
        
    def check_if_host_defined_in_nim(self, server_sn):
        '''check if the host is defined in nim server'''
        self.wait_for_locked_begin(server_sn)
        self.wait_for_locked_end(server_sn)
        check_host_defined_cmd = "lsnim -l %s" % server_sn
        cmd_ret_val = self.cmd_output(check_host_defined_cmd)
        cmd_ret_val_str = cmd_ret_val[0]
        str_to_match = "%s:" % server_sn
        indx_find = cmd_ret_val_str.find(str_to_match)
        finded_ret_val = False
        if 0 == indx_find:
            finded_ret_val = True
            
        return finded_ret_val
    
            
    def if_nim_definition_locked(self, server_sn):
        '''
        Get the lock status of nim resource
        '''
        check_host_defined_cmd = "lsnim -l %s" % server_sn
        cmd_ret_val = self.cmd_output(check_host_defined_cmd)
        cmd_ret_val_str = cmd_ret_val[0]
        str_to_match = ["locked"]
        
        # Two conditions must both match
        finded_ret_val = False
        for chk_itm in str_to_match:
            indx_find = cmd_ret_val_str.find(chk_itm)       
            if indx_find >= 0:
                finded_ret_val = True
                break
                            
        return finded_ret_val
    
    
    def wait_for_locked_begin(self, server_sn):
        count_to_wait = 5 
        count = 0
        while not self.if_nim_definition_locked(server_sn) and count < count_to_wait:
            count += 1
            time.sleep(1)
            
    def wait_for_locked_end(self, server_sn):
        while self.if_nim_definition_locked(server_sn):
            time.sleep(1)
        
        
    def check_if_host_resource_defined_in_nim(self, server_sn):
        '''
        To check if the following field already in the nim definition
        '''
        self.wait_for_locked_begin(server_sn)
        self.wait_for_locked_end(server_sn)
        check_host_defined_cmd = "lsnim -l %s" % server_sn
        cmd_ret_val = self.cmd_output(check_host_defined_cmd)
        cmd_ret_val_str = cmd_ret_val[0]
        str_to_match = ["bosinst_data", "mksysb", "spot", "nim_script"]
        
        # Two conditions must both match
        finded_ret_val = True
        for chk_itm in str_to_match:
            indx_find = cmd_ret_val_str.find(chk_itm)       
            if indx_find >= 0:
                finded_ret_val = finded_ret_val and True
            else:
                finded_ret_val = finded_ret_val and False
                break
                            
        return finded_ret_val
               
    def define_server_in_nim(self, server_sn):
        '''define a server in nim server'''
        cmd = 'nim -o define -t standalone -a platform=chrp \
               -a if1="nim-net %s 0" -a netboot_kernel=64 \
               -a cable_type1=bnc -a connect=shell %s' % (server_sn, server_sn)
        self.exec_cmd(cmd)
        
        
    def assign_resource_to_server(self, server_sn):
        '''assign resource to a server'''
        cmd = 'nim -o bos_inst -a source=mksysb -a spot=vios4_spot \
               -a mksysb=vios4_mksysb -a bosinst_data=vios4_bosinst \
               -a boot_client=no  -a accept_licenses=yes %s' % server_sn
        self.exec_cmd(cmd)

    def remove_record_from_file(self, server_name):
        '''create system connection'''
        self.backup_hosts_file()
        cmd = "sed '/%s/d' /etc/hosts_file.saveold > /etc/hosts" % (server_name)
        self.exec_cmd(cmd)


    def clean_defined_resource_by_ip(self, ip):
        '''
        get server sn by matching ip in hosts file
        '''
        ip_matched_line = self.check_file_content(ip, "/etc/hosts")
        if ip_matched_line:
            _ip, _sn = ip_matched_line.split()
            self.remove_allocated_resource_in_nim(_sn)
        
        
    def append_record_into_file(self, server_ip, server_name):
        '''create system connection'''
        cmd = "echo %s\t%s >> /etc/hosts" % (server_ip, server_name)
        self.exec_cmd(cmd)


    def backup_hosts_file(self):
        '''recover profile for a server which specified by server name'''
        cmd = "cp /etc/hosts /etc/hosts_file.saveold"
        DebugLog.info_print("backup hosts file")
        self.exec_cmd(cmd)
        
    
    def remove_record_from_file_by_ip(self, server_ip):
        '''create system connection'''
        #self.clean_defined_resource_by_ip(server_ip)
        self.backup_hosts_file()
        cmd = "sed '/%s/d' /etc/hosts_file.saveold > /etc/hosts" % (server_ip)
        self.exec_cmd(cmd)

    
    def check_file_content(self, check_text, file_name):
        '''grep  check_text in file_name'''
        try:
            cmd = "grep %s %s" % (check_text, file_name)
            ret_val = self.cmd_output(cmd)
            return ret_val[0]
        except:
            return None
    
    
    def exec_cmd(self, cmd, with_output=False):
        '''execute cmd in the session'''
        if not with_output:
            self.remote_session.interactive_cmds(cmd, "#  #", False)
        else:
            return self.remote_session.interactive_cmds(cmd, "#  #", True)
        
    
    def cmd_output(self, cmd):
        '''execute the command the return the output'''
        return self.exec_cmd(cmd, with_output=True)
        
    
    

        