#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
PD ssh session test
'''

import sys
import time
import logging
import paramiko

import DebugLog
import os
from os import path
from ErrorHandler import PackagePath_NotExists_Error, ConnectFail_Error


class Login_Timeout_Exception(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "Login timeout exception occurs"



class Remote_Session(object):
    '''
    test pexpect to emulate the session
    '''

    def __init__(self, target, password):
        '''
        connectSSH the target
        Use pexpect to implement the ssh connection;
        Would replace it with paramiko module
        '''
        self.target = target
        self.password = password
            
        try:
            self.connectSSH()
        except Exception, e:
            DebugLog.debug_print_level1(e)
            raise ConnectFail_Error("Server connection failed.")

        
    def connectSSH(self):
        '''establish a connection between the client and the server'''
        if DebugLog.is_verbose:
            logging.getLogger("paramiko").setLevel(logging.DEBUG)
        else:
            logging.getLogger("paramiko").setLevel(logging.WARN)
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname=self.target,
                           username='root',
                           password=self.password)
        
        self.channel = self.client.invoke_shell()
        self.stdin = self.channel.makefile('wb')
        self.stdout = self.channel.makefile('rb')
#         default_timeout = self.channel.gettimeout()
#         DebugLog.info_print("=======================================")
#         if default_timeout:
#             DebugLog.info_print("The timeout is %d" % default_timeout)
#         else:
#             DebugLog.info_print("The channel is blocking mode, and timeout is None")
#         DebugLog.info_print("=======================================")
        #self.channel.settimeout(default_timeout)

 
    def open_sftp(self):
        '''Get the sftp client'''
        self.ftpclient = self.client.open_sftp()
        return self.ftpclient
    
    def sftp_putfile(self, srcfile, dstfile):
        self.ftpclient.put(srcfile, dstfile)
        
    def sftp_putall(self, srcdir, dstdir, force_override=False):
        '''put all directory into the dest directory'''
        self.connectSSH()
        self.open_sftp()
        #  recursively upload a full directory
        localpath = srcdir
        remotepath = dstdir
        
        if not os.path.exists(localpath):
            raise PackagePath_NotExists_Error("Path does not exist.")
        
        os.chdir(os.path.split(localpath)[0])
        parent=os.path.split(localpath)[1]

            
        target_dir = os.path.join(remotepath, parent).replace("\\", '/')
        try:
            self.ftpclient.stat(target_dir)
            if not force_override:
                    DebugLog.info_print("%s exists." % target_dir)
                    return
        except:
            
            '''the target folder dees not exist'''       
            for walker in os.walk(parent):
                try:
                    self.sftp_mkdir(os.path.join(remotepath,walker[0]).replace("\\", '/'))
                except:
                    pass
                
                DebugLog.info_print("copy the dir %s" % walker[0])
                for wfile in walker[2]:
                    self.sftp_putfile(os.path.join(walker[0],wfile),os.path.join(remotepath,walker[0],wfile).replace("\\", '/'))

        DebugLog.info_print("copy %s to %s successfully." % (srcdir, dstdir))

    def sftp_mkdir(self, dirname):
        #self.connectSSH()
        #self.open_sftp()
        try:
            self.ftpclient.stat(dirname)
        except Exception, err:
            DebugLog.info_print("Create the the dir %s" % dirname)
            self.ftpclient.mkdir(dirname)
    
    def set_file_executable(self, filename):
        '''set file as executable'''
        try:
            self.client.exec_command("chmod a+x %s" % filename)
            DebugLog.info_print("assign execute permission successfully")
        except :
            DebugLog.info_print("assign execute permission failed")
            raise 
        
        
    def launch_script_to_install(self, script_file, cmd_input_list, carriage='\n'):
        '''to deal the installation interactivly'''
        self.connectSSH()
        time.sleep(0.1)
        
        DebugLog.debug_print_level2("in the launch_script_to_install")
        DebugLog.debug_print_level2("send the commands %s" % script_file)
        
        #self.channel.send(script_file+carriage)
        for cmd in cmd_input_list:
            skip_step = False

            if cmd[1]:
                buf = ''
                while not buf.endswith(cmd[1]):
                    time.sleep(0.5)
                    buf += self.channel.recv(1920)
                    if cmd[2] and cmd[2] in buf:
                        skip_step = True
                        break
                    DebugLog.info_print("Now the buf is : " + buf)
            
            if not skip_step:
                self.channel.send(cmd[0]+carriage)
                DebugLog.info_print("send the cmd: %s" % cmd[0])
            

    def check_if_app_launched(self, appdesc):
        '''check if the app process startup'''
        check_result = self.cmd_output('ps -ef | grep "%s" | grep -v grep; echo $?' %appdesc)
        return check_result.endswith("0")
        
    
    def start_app_mannually(self, app):
        '''start up app'''
        appdesc = app.lower()
        if appdesc.endswith("powerdirector"):
            #self.cmd_output("cd /powerdirector/tomcat/bin; ./startup.sh")
            self.interactive_cmds("cd /powerdirector/tomcat/bin; nohup ./startup.sh > /dev/null 2>&1 &",
                                  "# # #")
       # elif appdesc.endswith("powerdirectorei"):
       #     self.interactive_cmds("cd /powerdirectorei/tomcat/bin; nohup ./startup.sh > /dev/null 2>&1 &",
       #                           "# # #")
       # elif appdesc.endswith("powerdirectorha"):
       #     self.interactive_cmds("cd /powerdirectorha/tomcat/bin; nohup ./startup.sh > /dev/null 2>&1 &",
       #                           "# # #")
        elif appdesc.endswith("pdhelper"):
            self.interactive_cmds("cd /pdhelper/tomcat/bin; nohup ./startup.sh > /dev/null 2>&1 &",
                                  "# # #")
            
            
            
    def sendline(self, cmd):
        '''
        return the command output
        '''
        time.sleep(0.1)
        self.stdself.client.sendline(cmd)
        line_str = self.client.readline()
        DebugLog.debug_print("The line is %s" % line_str)
        return line_str

    def cmd_output(self, cmd):
        '''execute the command, and return the output'''
        return self.cmd_output_close(cmd, False)

        
    def cmd_output_close(self, cmd, finished_and_close=True):
        '''execute the command, and return the output'''
        self.connectSSH()
        time.sleep(0.1)
        DebugLog.info_print("The cmd is '%s'" % cmd)
        self.stdin, self.stdout, self.stderr = self.client.exec_command(cmd)
        DebugLog.info_print("The cmd %s has been executed." % cmd)
        buf_out = self.stdout.read().strip()
        buf_err = self.stderr.read().strip()
        DebugLog.info_print("The cmd output is %s" % buf_out)
        DebugLog.info_print("The cmd error output is %s" % buf_err)
        
        DebugLog.info_print(DebugLog.CMD_SEP)
        DebugLog.info_print("#>" + cmd)
        DebugLog.info_print(buf_out)
        DebugLog.info_print(buf_err)
        DebugLog.info_print(DebugLog.CMD_SEP)
        
        if finished_and_close:
            self.stdin.close()
            self.stdout.close()
            self.stderr.close()
            self.client.close()
            
        return buf_out 
    
    
#     def interactive_shell(self, cmd):
#         '''lauch interactive shell to execute commands'''
#         chan = self.client.invoke_shell()
#         print(repr(self.client.get_transport()))
#         print('*** Here we go!\n')
#         interactive.interactive_shell(chan)
#         chan.close()
#         self.client.close()        

    def interactive_cmd_output(self, cmd):
        '''execute the command, and return the output'''
        self.connectSSH()
        time.sleep(0.1)
        cmds = cmd.split(';')
        
        DebugLog.debug_print_level2("in the interactive_cmd_output")
        DebugLog.info_print("send the commands %s" % cmds[0])
        self.channel.send(cmds[0]+"\n")
        #self.stdin.write(cmds[0]+"\n")
        #self.stdin.flush()
         
        buf = ''
        while not buf.endswith('$ '):
            buf += self.channel.recv(1920)
            DebugLog.info_print("Now the buf is : " + buf)
        
        for indx in range(len(cmds)):
            if indx != 0:
                self.channel.send(cmds[indx]+"\n")   
            
        buf = ''
        while not buf.endswith('$ '):
            buf += self.channel.recv(1920)
            DebugLog.info_print("Now the buf is : " + buf)
        
        DebugLog.debug_print_level2("get the output")
        #buf_out = self.stdout.read()

        DebugLog.debug_print_level2(buf)
        buf_out = buf.split('\r\n')
        buf_out = "%s" % buf_out[1:-1]
             
        return buf_out 
        
    def interactive_cmds(self, cmd, expect_prompt, with_return=False):
        '''execute the command, and return the output'''
        self.connectSSH()
        time.sleep(0.1)
        cmds = cmd.split(';')
        expect_prompts = expect_prompt.split()
        
        DebugLog.debug_print_level2("in the interactive_cmd")
        DebugLog.debug_print_level2("send the commands %s" % cmds[0])
        
        #DebugLog.info_print("The current prompt is %s" % self.channel.)
        #self.channel.send(cmds[0]+"\n")
        expect_idx = 0
        buf = ''
        
        for indx in range(0, len(cmds)):
            #if indx != 0:
            self.channel.send(cmds[indx]+"\n") 
            buf = self.channel.recv(1920)
            expect_idx += 1  
            
            while not buf.strip().endswith(expect_prompts[expect_idx]):
                buf = self.channel.recv(1920)
                DebugLog.info_print("Now the buf is : " + buf)

        
        if with_return:
            DebugLog.debug_print_level2("get the output")
            DebugLog.debug_print_level2(buf)
            buf_out = buf.split('\r\n')
            buf_out = "%s" % buf_out[1:-1]
            return buf_out
        
                
    def close(self):
        self.client.close()

    
    def get_os_name(self):
        '''return the os name'''
        return self.cmd_output("uname")
    

    def goto_super_mode(self):
        '''go into super mode'''
        self.interactive_cmd_output("su - padmin")
    
    
    def exit_super_mode(self):
        '''exit the super mode'''
        self.interactive_cmd_output("exit")
    
    
    def get_pwd_result(self):
        '''return pwd result'''
        return self.interactive_cmd_output("pwd")
        
    def get_os_vesion(self):
        '''return os platform version'''
        #self.goto_super_mode()
        version = self.interactive_cmd_output("su - padmin;ioslevel")
        #version = self.cmd_output("oslevel")
        #self.get_pwd_result()
        #self.exit_super_mode()
        
        return version
    

 
