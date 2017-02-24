#--*-- coding:utf-8 --*--
'''
Created on 2015��5��8��

@author: stm
'''

from base.engine import EngineBase

import string


from utils import DebugLog
from utils.ErrorHandler import ConfigFileError
from base.cmdmsg import CMDMsg, PREPAREHOSTSFILE, DEFINESERVER, ASSIGNRESOURCE, \
                        CHECKHOSTSFILE, CHECKDEFINEDSERVER, CHECKASSIGNEDRESOURCE, \
                        CLEANNIMRESOURCE, CHECKCLEANSTATUS
                        
from engine.sessions.nimcli_session import NIM_CLI
from base.vdstate import CREATEVIOSLPAR_STAT, PRGRS_INPROGRESS, PRGRS_FINISHED,\
    PREPAREHOSTSFILE_STAT, DEFINESERVER_STAT, ASSIGNRESOURCE_STAT,\
    CLEAN_NIM_RESOURCE_STAT


class NIMEng(EngineBase):
    '''
    classdocs
    '''

    def __init__(self, vd_comm_cnt, vd_config):
        '''
        NIM Server Engine to deal with nim resource definition
        '''
        DebugLog.info_print("NIMEng initialized")
        EngineBase.__init__(self, vd_comm_cnt, vd_config)
        
        try:
            self.nimserver_ip = self.vd_config.get('topo', 'nimserver_ip')
            self.nimserver_username = self.vd_config.get('topo', 'nimserver_username')
            self.nimserver_passwd = self.vd_config.get('topo', 'nimserver_passwd')
            
            self.nimres_spot_res = self.vd_config.get("nim_resource_definition", "spot_res")
            self.nimres_mksysb_res = self.vd_config.get("nim_resource_definition", "mksysb_res")
            self.nimres_bosinst_data_res = self.vd_config.get("nim_resource_definition", "bosinst_data_res")
        except:
            raise ConfigFileError()

        
    def check_hosts_file(self, server_id, data):
        '''
        add records in /etc/hosts
        data: [ip, sn]
        '''

        _finished = False
        resp_msg = ''
        
        nim_cli = NIM_CLI(self.nimserver_ip, self.nimserver_passwd)
        
        data_list = eval(data)

        server_ip, server_name = (data_list[0], data_list[1])
        chk_result = nim_cli.check_file_content(server_ip, "/etc/hosts")
        if chk_result is not None and not (chk_result.find(server_ip) == -1):
            _finished = True
        
        if _finished:
            resp_msg = EngineBase.get_post_phase_progress_msg(server_id, 
                                           PREPAREHOSTSFILE_STAT, 
                                           PRGRS_FINISHED, 
                                           PREPAREHOSTSFILE)
            
        else:
            resp_msg = EngineBase.get_post_phase_progress_msg(server_id, 
                                           PREPAREHOSTSFILE_STAT, 
                                           PRGRS_INPROGRESS, 
                                           PREPAREHOSTSFILE)
        if resp_msg:
            self.vd_comm_cnt.postMessage(resp_msg)
    
    def prepare_hosts_file(self, server_id, data):
        '''
        add records in /etc/hosts
        data: [ip, sn]
        '''
        resp_msg = EngineBase.get_post_phase_progress_msg(server_id, 
                                           PREPAREHOSTSFILE_STAT, 
                                           PRGRS_INPROGRESS, 
                                           PREPAREHOSTSFILE)
        self.vd_comm_cnt.postMessage(resp_msg)
        
        nim_cli = NIM_CLI(self.nimserver_ip, self.nimserver_passwd)
        
        data_list = eval(data)
        #loop_cnt = len(data_list)
        #for loop_idx in range(loop_cnt):
        from utils.FileLock import FileLock

        with FileLock("modify_hosts_file.lock", timeout=300):
            server_ip, server_name = (data_list[0], data_list[1])
            nim_cli.remove_record_from_file(server_name)
            nim_cli.remove_record_from_file_by_ip(server_ip)
            nim_cli.append_record_into_file(server_ip, server_name)
    
        resp_msg = EngineBase.get_post_phase_progress_msg(server_id, 
                                           PREPAREHOSTSFILE_STAT, 
                                           PRGRS_FINISHED, 
                                           PREPAREHOSTSFILE)           

        self.vd_comm_cnt.postMessage(resp_msg)
        
#         msg = self.msg_decoder.encodeMsg(CMDMsg.getCMD(PREPAREHOSTSFILE), '_')
#         self.vd_comm_cnt.postMessage(msg)
        
    def _deal_with_data(self, server_id, data, func, with_params=True, post_cmd=None):
        '''
        as for data is a list type, and let func to deal with all the data
        @data: list type which contains server's serial_num
        '''
        DebugLog.debug_print_level1("Connect nim server session")
        nim_cli = NIM_CLI(self.nimserver_ip, self.nimserver_passwd)
        data_list = eval(data)
        loop_cnt = len(data_list)
        for loop_idx in range(loop_cnt):
            func_name = "nim_cli."+func
            DebugLog.debug_print_level1("Call nim server function %s" % func_name)
            if with_params:
                resp = eval(func_name)(data_list[loop_idx])
            else:
                resp = eval(func_name)()
                
            if post_cmd:
                msg = self.msg_decoder.encodeMsg(post_cmd, server_id, resp)
                DebugLog.debug_print_level1(msg)
                self.vd_comm_cnt.postMessage(msg)
        

    def define_server_in_nim(self, server_id, data):
        '''define server in nim server using the server's serial num which is in the data list'''
        resp_msg = EngineBase.get_post_phase_progress_msg(server_id, 
                                           DEFINESERVER_STAT, 
                                           PRGRS_INPROGRESS, 
                                           DEFINESERVER)
        self.vd_comm_cnt.postMessage(resp_msg)
        
        nim_cli = NIM_CLI(self.nimserver_ip, self.nimserver_passwd)
        
        data_list = eval(data)
        server_sn = data_list[0]

        #nim_cli.remove_allocated_resource_in_nim(server_sn)
        nim_cli.define_server_in_nim(server_sn)
        
        
    def clean_nim_define(self, server_id, data):
        '''clean nim define'''
        resp_msg = EngineBase.get_post_phase_progress_msg(server_id, 
                                           CLEAN_NIM_RESOURCE_STAT, 
                                           PRGRS_INPROGRESS, 
                                           CLEANNIMRESOURCE)
        self.vd_comm_cnt.postMessage(resp_msg)
        
        nim_cli = NIM_CLI(self.nimserver_ip, self.nimserver_passwd)
        
        data_list = eval(data)
        server_sn = data_list[0]
        nim_cli.remove_allocated_resource_in_nim(server_sn)
        
        
        
    def check_if_server_defined_in_nim(self, server_id, data):
        '''use lsnim -l command to check if the server existed in nim defined resource'''
        _finished = False
        resp_msg = ''
        
        nim_cli = NIM_CLI(self.nimserver_ip, self.nimserver_passwd)

        data_list = eval(data)
        server_sn = data_list[0]
        _finished = nim_cli.check_if_host_defined_in_nim(server_sn)
        
        if _finished:
            resp_msg = EngineBase.get_post_phase_progress_msg(server_id, 
                                           DEFINESERVER_STAT, 
                                           PRGRS_FINISHED, 
                                           DEFINESERVER)
            
        else:
            resp_msg = EngineBase.get_post_phase_progress_msg(server_id, 
                                           DEFINESERVER_STAT, 
                                           PRGRS_INPROGRESS, 
                                           DEFINESERVER)
        if resp_msg:
            self.vd_comm_cnt.postMessage(resp_msg)
        

    def check_if_host_resource_assigned_in_nim(self, server_id, data):
        '''use lsnim -l command to check if the server existed in nim defined resource'''
        _finished = False
        resp_msg = ''
        
        nim_cli = NIM_CLI(self.nimserver_ip, self.nimserver_passwd)

        data_list = eval(data)
        server_sn = data_list[0]
        _finished = nim_cli.check_if_host_defined_in_nim(server_sn)
        
        if _finished:
            resp_msg = EngineBase.get_post_phase_progress_msg(server_id, 
                                           ASSIGNRESOURCE_STAT, 
                                           PRGRS_FINISHED, 
                                           ASSIGNRESOURCE)           
        else:
            resp_msg = EngineBase.get_post_phase_progress_msg(server_id, 
                                           ASSIGNRESOURCE_STAT, 
                                           PRGRS_INPROGRESS, 
                                           ASSIGNRESOURCE)
        if resp_msg:
            self.vd_comm_cnt.postMessage(resp_msg)
            
    
    def assign_server_resource(self, server_id, data):
        '''define server in nim server using the server's serial num which is in the data list'''
        resp_msg = EngineBase.get_post_phase_progress_msg(server_id, 
                                           ASSIGNRESOURCE_STAT, 
                                           PRGRS_INPROGRESS, 
                                           ASSIGNRESOURCE)
        self.vd_comm_cnt.postMessage(resp_msg)
        
        nim_cli = NIM_CLI(self.nimserver_ip, self.nimserver_passwd)
        
        data_list = eval(data)
        #loop_cnt = len(data_list)
        #for loop_idx in range(loop_cnt):
        server_sn = data_list[0]
        nim_cli.assign_resource_to_server(server_sn)

    
    
    def check_nim_resouce(self, _server_id, data):
        '''use lsnim -l command to check if the server existed in nim defined resource'''
        _finished = False
        resp_msg = ''
        
        nim_cli = NIM_CLI(self.nimserver_ip, self.nimserver_passwd)

        data_list = eval(data)
        server_sn = data_list[0]
        _found = nim_cli.check_if_host_defined_in_nim(server_sn)
        
        if _found:
            resp_msg = EngineBase.get_post_phase_progress_msg(_server_id, 
                                           CLEAN_NIM_RESOURCE_STAT, 
                                           PRGRS_INPROGRESS, 
                                           CLEANNIMRESOURCE)           
        else:
            resp_msg = EngineBase.get_post_phase_progress_msg(_server_id, 
                                           CLEAN_NIM_RESOURCE_STAT, 
                                           PRGRS_FINISHED, 
                                           CLEANNIMRESOURCE)
            nim_cli.remove_record_from_file(server_sn)
        
        if resp_msg:
            self.vd_comm_cnt.postMessage(resp_msg)
    
    
    def process_message(self, msg):
        DebugLog.info_print("Got the command tranfering in hmc engine")
        cmd, _server_id, data = self.msg_decoder.decodeMsg(msg)
        if CMDMsg.getCMD(PREPAREHOSTSFILE) == cmd:
            self.prepare_hosts_file(_server_id, data)
        elif  CMDMsg.getCMD(DEFINESERVER) == cmd:
            self.define_server_in_nim(_server_id, data)
        elif CMDMsg.getCMD(ASSIGNRESOURCE) == cmd:
            self.assign_server_resource(_server_id, data)
        elif CMDMsg.getCMD(CHECKHOSTSFILE) == cmd:
            self.check_hosts_file(_server_id, data)
        elif CMDMsg.getCMD(CHECKDEFINEDSERVER) == cmd:
            self.check_if_server_defined_in_nim(_server_id, data)
        elif CMDMsg.getCMD(CHECKASSIGNEDRESOURCE) == cmd:
            self.check_if_host_resource_assigned_in_nim(_server_id, data)
        elif CMDMsg.getCMD(CLEANNIMRESOURCE) == cmd:
            self.clean_nim_define(_server_id, data)
        elif CMDMsg.getCMD(CHECKCLEANSTATUS) == cmd:
            self.check_nim_resouce(_server_id, data)
               
            
        
