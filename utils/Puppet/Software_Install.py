# -*- coding: utf-8 -*-
'''
Created on 2014��12��15��

@author: stm
'''

from BaseCheck import BaseCheck
import os
import shutil
import DebugLog
import time
from ErrorHandler import PackagePath_Error, PackageVersionNumber_Error,\
    DiskSizeNotEnough_Error
import string
import re

class Software_Install(BaseCheck):
    '''
    Install the applictaion
    '''
    def install_xeap(self):
        '''
        Would install xeap software
        '''
        print "Would install xeap software"
        self.install_pd_sw("xeap")
    
    
    def install_pd3(self):
        '''
        Would install pd3 software
        '''
        print "Would install PD3 software"
        self.install_pd_sw("3.0")
        
    
    def install_pd25(self):
        '''
        Would install pd2.5 software
        '''
        print "Would install PD2.5 software"
        self.install_pd_sw("2.5")
        
    
    def install_pd26(self):
        '''
        Would install pd2.6 software
        '''
        print "Would install PD2.6 software"
        self.install_pd_sw("2.6")
        
    
    def get_pd2_package_path(self):
        '''get the pd2 package path'''
        path = ''
        try:
            path = self.config.get('pd2_packages', 'package_folder')
        except:
            raise PackagePath_Error()
        
        return path
        
    
    def get_pd2_package_version_number(self):
        '''get the pd2 package version number'''
        version_number = ''
        
        try:
            version_number = os.environ['PACKAGE_VERSION_NUMBER']
        except:
            raise PackageVersionNumber_Error()
        
        return version_number 
    
    
    def check_root_disk_size(self, exp_size):
        '''get the root disk free size'''
        SEARCH_PAT = re.compile(r'(\d+)\s*')
        s_free_size = self.remote_session.cmd_output("df -g / | tail -1 | awk '{print $3}'")
        free_size = int(string.atof(s_free_size))
        pattern_search = SEARCH_PAT.search(exp_size)
        expect_size = 0
        if pattern_search:
            expect_size = int(pattern_search.group(1))
            
        DebugLog.info_print("The current free size is %dG, and the expect size is %dG" % 
                            (free_size, expect_size))
        if free_size < expect_size:
            raise DiskSizeNotEnough_Error()
    
        DebugLog.check_passed("Disk size")

    def install_PowerDirector(self, sw_dst_package_path, parent, exec_file):
        # input command list format: 
        # "command"
        # "expectation string "
        # "secondary expectation string": optional check string
        DebugLog.info_print_banner("install PowerDirector")
        script_file = os.path.basename(exec_file)
        pd_install_seq = (("cd %s/%s" % (sw_dst_package_path, parent),  None,  None),
                          ("./%s" % script_file, None, None),
                          ("1", "xit please input x : ", None),
                          ("2", "turn please input x : ", None),
                          ("y", "o you want uninstall PowerDirector? (y/n or yes/no): ", 
                                "The PowerDirector is not installed"),
                          ("1", "eturn please input x : ", None),
#                          ("1", "o you want continue to install PowerDirector? (y/n or yes/no): ", False),
                          ("x", "eturn please input x : ", None),
                          ("x", "xit please input x : ", None),
                          )
        
        self.remote_session.launch_script_to_install(exec_file, pd_install_seq)
        
    
    
    def install_PowerDirectorHelper(self, sw_dst_package_path, parent, exec_file):
        '''install PowerDirectorHelper'''
        DebugLog.info_print_banner("install PowerDirectorHelper")
        script_file = os.path.basename(exec_file)
        pd_install_seq = (("cd %s/%s" % (sw_dst_package_path, parent), None,  None),
                          ("./%s" % script_file, None, None),
                          ("2", "xit please input x : ", None),           # select the PowerDirectorHelper
                          ("2", "turn please input x : ", None),          # uninstall it
                          ("y", "o you want uninstall PowerDirectorHelper? (y/n or yes/no): ", 
                                "The PowerDirectorHelper is not installed"),    # select yes or continue
                          ("1", "eturn please input x : ", None),         # install it
#                          ("1", "o you want continue to install PowerDirector? (y/n or yes/no): ", False),
                          ("x", "eturn please input x : ", None),         # return the previous screen/menu
                          ("x", "xit please input x : ", None),           # exit the menu
                          )
        
        self.remote_session.launch_script_to_install(exec_file, pd_install_seq)
    
    
    def install_PowerDirectorHA(self, sw_dst_package_path, parent, exec_file):
        '''install PowerDirectorHA'''
        DebugLog.info_print_banner("install PowerDirectorHA")
        script_file = os.path.basename(exec_file)
        pd_install_seq = (("cd %s/%s" % (sw_dst_package_path, parent), None,  None),
                          ("./%s" % script_file, None, None),
                          ("3", "xit please input x : ", None),           # select the PowerDirectorHA
                          ("2", "turn please input x : ", None),          # uninstall it
                          ("y", "o you want uninstall PowerDirectorHA? (y/n or yes/no): ", 
                                "The PowerDirectorHA is not installed"),    # select yes or continue
                          ("1", "eturn please input x : ", None),         # install it
#                          ("1", "o you want continue to install PowerDirector? (y/n or yes/no): ", False),
                          ("x", "eturn please input x : ", None),         # return the previous screen/menu
                          ("x", "xit please input x : ", None),           # exit the menu
                          )
        
        self.remote_session.launch_script_to_install(exec_file, pd_install_seq)
    
    
    def install_PowerDirectorEI(self, sw_dst_package_path, parent, exec_file):
        '''install PowerDirectorEI'''
        DebugLog.info_print_banner("install PowerDirectorEI")
        script_file = os.path.basename(exec_file)
        pd_install_seq = (("cd %s/%s" % (sw_dst_package_path, parent), None,  None),
                          ("./%s" % script_file, None, None),
                          ("4", "xit please input x : ", None),           # select the PowerDirectorEI
                          ("2", "turn please input x : ", None),          # uninstall it
                          ("y", "o you want uninstall PowerDirectorEI? (y/n or yes/no): ", 
                                "The PowerDirectorEI is not installed"),    # select yes or continue
                          ("1", "eturn please input x : ", None),         # install it
#                          ("1", "o you want continue to install PowerDirector? (y/n or yes/no): ", False),
                          ("x", "eturn please input x : ", None),         # return the previous screen/menu
                          ("x", "xit please input x : ", None),           # exit the menu
                          )
        
        self.remote_session.launch_script_to_install(exec_file, pd_install_seq)
    
    
    
    def check_if_PowerDirectorHelper_is_started(self):
        self._check_if_pd_app_is_started("pdhelper")
    
    
    def exec_install_pd25(self, sw_dst_package_path, parent, exec_file):
        '''install powerdirector 2.5 '''
        self.install_PowerDirector(sw_dst_package_path, parent, exec_file)
        self.check_func_list.append(self.check_if_powerdirector_is_started)
        self.install_PowerDirectorHelper(sw_dst_package_path, parent, exec_file)
        self.check_func_list.append(self.check_if_PowerDirectorHelper_is_started)
    
    
    def check_if_PowerDirectorHA_is_started(self):
        self._check_if_pd_app_is_started("powerdirectorha")
    
    
    def check_if_PowerDirectorEI_is_started(self):
        self._check_if_pd_app_is_started("powerdirectorei")
    
    
    def exec_install_pd26(self, sw_dst_package_path, parent, exec_file):
        '''install powerdirector 2.6 '''
        self.install_PowerDirector(sw_dst_package_path, parent, exec_file)
        self.check_func_list.append(self.check_if_powerdirector_is_started)
        self.install_PowerDirectorHelper(sw_dst_package_path, parent, exec_file)
        self.check_func_list.append(self.check_if_PowerDirectorHelper_is_started)
        self.install_PowerDirectorHA(sw_dst_package_path, parent, exec_file)
        self.check_func_list.append(self.check_if_PowerDirectorHA_is_started)
        self.install_PowerDirectorEI(sw_dst_package_path, parent, exec_file)
        self.check_func_list.append(self.check_if_PowerDirectorEI_is_started)
             
     
    def check_if_pd3_is_started(self):
        self._check_if_pd_app_is_started("pd3", pd3=True)
    
    def check_if_xeap_is_started(self):
        self._check_if_pd_app_is_started("xeap", pd3=True)
    
    
    def exec_install_pd3(self, sw_dst_package_path, parent, exec_file):
        '''install and start PD3 '''
        DebugLog.info_print_banner("install PD3")
        script_file = os.path.basename(exec_file)
        dirname = os.path.dirname(exec_file)
        pd_install_seq = (("cd %s" % (dirname), None,  None),
                          ("./%s uninstall" % script_file, "# ", None),
                          ("./%s install" % script_file, "# ", None),
                          ("./%s config" % script_file, "# ", None),
                          ("exit", "# ", None), # to make sure the previous command can be executed successfully
                          )
        
        self.remote_session.launch_script_to_install(exec_file, pd_install_seq)
        
        self.check_func_list.append(self.check_if_pd3_is_started)

    def exec_install_xeap(self, sw_dst_package_path, parent, exec_file):
        '''install and start xeap '''
        DebugLog.info_print_banner("install xeap")
        script_file = os.path.basename(exec_file)
        dirname = os.path.dirname(exec_file)
        pd_install_seq = (("cd %s" % (dirname), None,  None),
                          ("./%s" % script_file, None, None),
                          ("3", "xit please input x :", None),                     # select the uninstall
                          ("y", "o you want to Uninstall all XEAP Product? (y/n or yes/no):", None),    # select yes or continue
                          ("1", "xit please input x :", None),                     # select install XEAP Environment
                          ("y", "o you want to install XEAP Environment? (y/n or yes/no):", None),    # select yes or continue
                          ("2", "xit please input x :", None),                     # select install XEAP Main Function
                          ("y", "o you want to install XEAP Main Function? (y/n or yes/no):",None),     # select yes or continue
                          #("x", "xit please input x :", None),                                     # exit the menu
                          ("exit", "# ", None),
                          )
        
        self.remote_session.launch_script_to_install(exec_file, pd_install_seq, carriage='\r')
        
        #import pdb; pdb.set_trace()
        self.check_func_list.append(self.check_if_xeap_is_started)    
        
       
    def check_if_powerdirector_is_started(self):
        '''to check if the powerdirector is installed and launched'''
        self._check_if_pd_app_is_started("powerdirector")
        
    
    def _check_if_pd_app_is_started(self, appname, pd3=False):
        '''to check if the powerdirector is installed and launched'''
        
        app_proc_name = "/%s/tomcat"
        start_app_manually_msg = "Start %s manually." % appname
        start_app_success_msg =  "Start %s successfully." % appname
        start_app_failed_msg =  "Start %s failed." % appname
        if pd3:
            app_proc_name = '/powerdirector/apache-tomcat-7.0.52'
        else:
            app_proc_name = app_proc_name % appname
            
        app_is_started = False
        trycounter = 0
        while not app_is_started and trycounter < 2:
            app_is_started = self.remote_session.check_if_app_launched(app_proc_name)
            time.sleep(10)
            if not app_is_started:
                DebugLog.info_print(start_app_manually_msg)
                self.remote_session.start_app_mannually(appname)
            trycounter += 1
            
        if app_is_started:
            DebugLog.info_print(start_app_success_msg)
        else:
            DebugLog.info_print(start_app_failed_msg)
            
            
    def check_if_app_started(self):
        '''run the func check list'''
        if self.check_func_list:
            for func in self.check_func_list:
                func()
        
    
    def install_pd_sw(self, pd_major_ver):
        '''Install pd software using shell scripts'''
        #import pdb; pdb.set_trace()
        version = self.get_pd2_package_version_number()
        package_path = self.get_pd2_package_path()
        
        package_folder = "PD2.5_Build"
        install_func = None
        script_file = "install-powerdirector.sh"
        if pd_major_ver == '2.5':
            package_folder = "PD2.5_Build"
            install_func = self.exec_install_pd25
            package_name_prefix = "PDinstall"
        elif pd_major_ver == "2.6":
            package_folder = "PD2.6_Build"
            install_func = self.exec_install_pd26
            package_name_prefix = "PDinstall"
        elif pd_major_ver == "3.0":
            package_folder = "PD3_Build"
            install_func = self.exec_install_pd3
            package_name_prefix = "pd3install-redhat"
            script_file = "pd3install-redhat/pd3-install.sh"
        elif pd_major_ver == "xeap":
            package_folder = "XEAP_Build"
            install_func = self.exec_install_xeap
            package_name_prefix = "xeap-redhat-rpm"
            script_file = "xeap-redhat/xeap-install-all.sh"
            
        sw_src_package_path = os.path.join(package_path, package_folder, 
                                           "%s-%s" % (package_name_prefix, version))
        sw_dst_package_path = "/pd_temp_install"
        # sw_filename = "install-powerdirector.sh"
        
        # check the disk size > 2G
        #self.check_root_disk_size("2G")
        
        #import pdb;pdb.set_trace()

        # copy the software package to remote target
        self.remote_session.open_sftp()
        self.remote_session.sftp_mkdir(sw_dst_package_path)
        # test the sftp_putfile
        #sw_src_package_path = os.path.join(sw_src_package_path, sw_filename)
        #sw_dst_package_path = sw_dst_package_path +"/"+ sw_filename
        
        # to test if sw_dst_package_path exists on remote target
        
        self.remote_session.sftp_putall(sw_src_package_path, sw_dst_package_path)
        #sw_src_package_path_zfile = 
        
        # chmod + x the install script file
        localpath = sw_src_package_path
        remotepath = sw_dst_package_path
        
        parent=os.path.split(localpath)[1]
        
        target_file = os.path.join(remotepath, parent, script_file).replace("\\", '/')
        
        self.remote_session.set_file_executable(target_file)

        # interact the installation steps
        install_func(sw_dst_package_path, parent, target_file)
        
        # try 10 times to check if the app is started
        self.check_if_app_started()
        

            
            
            
        
