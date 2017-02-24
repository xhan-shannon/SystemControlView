#--*-- coding:utf-8 --*--
'''
Created on 2015��5��8��

@author: stm
'''
from utils import DebugLog
from base.msgcodec import MsgCodec
from abc import abstractmethod
from base.vdstate import CREATEVIOSLPAR_STAT, StateBase
from base.cmdmsg import CMDMsg


class EngineBase(object):
    '''
    The engine would deal with the command from UI or command line.
    And it would respond the result to UI or command listener.
    '''
#     objs  = {}
#     def __new__(cls, *args, **kv):
#         if cls in cls.objs:
#             return cls.objs[cls]
#         cls.objs[cls] = super(EngineBase, cls).__new__(cls)
#     
    
    def __init__(self, vd_comm_cnt, vd_config):
        '''
        Constructor
        '''
        DebugLog.info_print("EngineBase is initialized")
        self.msg_decoder = MsgCodec()
        self.vd_comm_cnt = vd_comm_cnt
        self.vd_config = vd_config
        
        
    @abstractmethod
    def process_message(self, msg):
        '''
        virtual method
        '''
        pass
        
    @staticmethod
    def get_post_phase_progress_msg(server_id, phase, progress, cmd):
        resp_state = [StateBase.get_state_const(phase), 
                      StateBase.get_state_progress_const_name(progress)]
        
        msg = MsgCodec().encodeMsg(CMDMsg.getCMD(cmd),
                                         server_id, 
                                         resp_state)
        DebugLog.debug_print_level1(msg)
        return msg