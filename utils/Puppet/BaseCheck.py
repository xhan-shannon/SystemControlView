# -*- coding: utf-8 -*-
'''
Created on 2014��12��18��

@author: stm
'''
import DebugLog
from remote_session import Remote_Session
import ConfigParser
import os
from ErrorHandler import ConfigFileError




class BaseCheck(object):
    '''
    The BaseCheck class do the basic task, such as connect remote target
    '''

    def __init__(self, target, password, with_config=True):
        '''
        connectSSH the target
        Use pexpect to implement the ssh connection;
        Would replace it with paramiko module
        '''
        self.target = target
        self.password = password

        self.remote_session = Remote_Session(target, password)
        self.check_func_list = []
        if with_config:
            self.config = ConfigParser.ConfigParser()
            self.config_file = self.__class__.__name__ + '.cfg'
            DebugLog.debug_print_level2("The self.config_file is " + self.config_file)
            cur_work_dir = os.getcwd()
            mid_dir = "utils/Puppet/"
            self.config_file = os.path.join(cur_work_dir, mid_dir, self.config_file)
            DebugLog.debug_print_level2("The self.config_file is " + self.config_file)
            if self.config_file and os.path.exists(self.config_file):
                self.config.read(self.config_file)
            else:
                raise ConfigFileError('%s not found' % (self.config_file))