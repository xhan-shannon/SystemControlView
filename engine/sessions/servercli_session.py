# -*- coding: utf-8 -*-
'''
Created on 2015��1��13��

@author: stm
'''


import time
from remote_session import Remote_Session
from utils import DebugLog
from utils.IPCheck import IPCheck


class Server_CLI(object):
    '''
    The class maintains the SSH command line interface connection
    which uses ssh session to access the server
    '''

    def __init__(self, target, password, with_config=True):
        '''
        connectSSH the target
        Use pexpect to implement the ssh connection;
        Would replace it with paramiko module
        '''
        self.target = target
        self.password = password
        username = 'root'

        self.remote_session = Remote_Session(self.target, username, self.password)      
 

    def set_default_ip_and_shutdown(self, server_sn, bshutdn=False):
        '''Changes a password for a managed system or a managed frame.'''
        result_log = []
        
        result_item1 = []
        
        set_ip_cmd = 'mktcpip -h %s -a 192.168.9.188 -i en0 -m 255.255.255.0 -g 192.168.9.1' \
                % server_sn
        if bshutdn:
            set_ip_cmd += " && shutdown -F "
#         else:
#             set_ip_cmd += " && exit"
        
        self.remote_session.send_cmd(set_ip_cmd)
        DebugLog.info_print(set_ip_cmd)

    
    
    
