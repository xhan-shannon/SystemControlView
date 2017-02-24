# -*- coding: utf-8 -*-
'''
Created on 2014��12��15��

@author: stm
'''

import DebugLog
import time
from BaseCheck import BaseCheck
from ErrorHandler import WrongOSTarget_Exception, WrongOSTargetVersion_Exception,\
    TemplateNotMounted_Exception, PowerDirectorNotInstalled_Exception,\
    DiskSizeNotEnough_Error
import re
import string



class Server_Check(BaseCheck):
    '''
    To check server if it can be deployed PD3
    ''' 
        
    def check_server_environment(self):
        '''
        Check the environment of server
        '''
        print "Called in Server_Check::check_server_environment."
        
        chk_point_id = 0
        # Point 1: make sure the OS platform is AIX
        chk_point_id = chk_point_id + 1
        os = self.remote_session.get_os_name()
        if "AIX" == os:
            DebugLog.stepinfo_idx("OS is AIX", chk_point_id)
        else:
            raise WrongOSTarget_Exception()
            
        
        #self.remote_session.interactive_shell('')
        time.sleep(2)
        # Point 2: make sure the OS platform version
        chk_point_id = chk_point_id + 1
        os_version = self.remote_session.get_os_vesion()
        if "2.2.3.1" <= os_version:
            DebugLog.stepinfo_idx("OS version >= 2.2.3.1", chk_point_id)
        else:
            raise WrongOSTargetVersion_Exception()
            
            
        # Point 3: make sure the template director is mounted
        chk_point_id = chk_point_id + 1
        template_mounted = self.remote_session.check_if_template_mounted()
        if not template_mounted:
            raise TemplateNotMounted_Exception()

        # Point 4: make sure the powerdirector is installed
        chk_point_id = chk_point_id + 1
        powerdirector_installed = self.remote_session.check_if_powerdirector_installed()
        if not powerdirector_installed:
            raise PowerDirectorNotInstalled_Exception()


    def assert_Linux_os(self):
        '''to make sure the os is Linux'''
        self.check_os_uname("Linux")
        DebugLog.check_passed("OS Type")
    
    
    def assert_AIX_os(self):
        '''to make sure the os is Linux'''
        self.check_os_uname("AIX")
        DebugLog.check_passed("OS Type")
        
            
    def check_os_uname(self, os_uname_expct):
        '''to make sure the os is Linux'''
        osname = self.remote_session.get_os_name()
        if os_uname_expct == osname:
            DebugLog.stepinfo("OS is %s" % os_uname_expct)
        else:
            raise WrongOSTarget_Exception(os_uname_expct)
    
    
    def check_root_disk_size(self, exp_size, AIX=True):
        '''get the root disk free size'''
        disksize_cmd = "df -g"
        if not AIX:
            disksize_cmd= "df -h"
            
        disksize_cmd += " / | tail -1 | awk '{print $3}'"
        SEARCH_PAT = re.compile(r'(\d+)\s*')
        s_free_size = self.remote_session.cmd_output(disksize_cmd)
        free_size_search = SEARCH_PAT.search(s_free_size)
        free_size = int(string.atof(free_size_search.group(1)))
        pattern_search = SEARCH_PAT.search(exp_size)
        expect_size = 0
        if pattern_search:
            expect_size = int(pattern_search.group(1))
            
        DebugLog.stepinfo("Disk free size")
        DebugLog.info_print("The current free size is %dG, and the expect size is %dG" % 
                            (free_size, expect_size))
        if free_size < expect_size:
            #raise DiskSizeNotEnough_Error()
            resize_cmd = "chfs -a size=+%sG /" % expect_size
            self.remote_session.cmd_output(resize_cmd)
    
        DebugLog.check_passed("Disk size ")