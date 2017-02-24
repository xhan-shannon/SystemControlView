#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
PD ssh session test
'''

import sys
import time
import logging
import paramiko


import os
from os import path

from utils import DebugLog
from utils.ErrorHandler import ConnectFail_Error


class Login_Timeout_Exception(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "Login timeout exception occurs"



class Remote_Session(object):
    '''
    test pexpect to emulate the session
    '''

    def __init__(self, target, username, password):
        '''
        connectSSH the target
        Use pexpect to implement the ssh connection;
        Would replace it with paramiko module
        '''
        self.target = target
        self.password = password
        self.username = username

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
                           username=self.username,
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
        # self.channel.settimeout(default_timeout)



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


    def interactive_cmds(self, cmd, expect_prompt, with_return=False):
        '''execute the command, and return the output'''
        self.connectSSH()
        time.sleep(0.5)
        cmds = cmd.split(';')
        expect_prompts = expect_prompt.split()
        splitter_for_return =expect_prompts[0]

        DebugLog.debug_print_level2("in the interactive_cmd")
        DebugLog.debug_print_level2("send the commands %s" % cmds[0])

        # DebugLog.info_print("The current prompt is %s" % self.channel.)
        # self.channel.send(cmds[0]+"\n")
        expect_idx = 0
        buf = ''

        for indx in range(0, len(cmds)):
            # if indx != 0:
            DebugLog.info_print("Session cmd: %s" % cmds[indx])
            self.channel.send(cmds[indx] + "\n")
            time.sleep(1)
            buf = self.channel.recv(1920)
            
            expect_idx += 1

            while not buf.strip().endswith(expect_prompts[expect_idx]):
                buf += self.channel.recv(1920)
                time.sleep(1)
                DebugLog.info_print("Now the buf is : " + buf)


        if with_return:
            DebugLog.debug_print_level2("get the output")
            DebugLog.debug_print_level2(buf)

            # Got the content between two '~>'
            con_list = buf.split(splitter_for_return)
            con = con_list[-2]

            splitter = '\r\n'
            if splitter in con:
                pass
            else:
                splitter = '\n'
            buf_out = con.split(splitter)
            buf_out = buf_out[1:-1]
            return buf_out

    def send_cmd(self, cmd):
        '''execute the command, and return the output'''
        self.connectSSH()
        time.sleep(0.5)
        cmds = cmd.split(';')

        DebugLog.info_print("Session cmd: %s" % cmd)
        self.channel.send(cmd + "\n")
        time.sleep(1)
        
        
    def close(self):
        self.client.close()
