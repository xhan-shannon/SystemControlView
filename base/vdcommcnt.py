#--*-- coding:utf-8 --*--

'''
Created on 2015��5��8��

@author: stm
'''
import Queue

import time
import string
from utils import DebugLog
from base.msgcodec import MsgCodec
from threading import Thread
from base.DelayedQueue import DelayedQueue

class VdCommCenter(object):
    '''VdCommCenter is the communication center for VIOS Deployment Tool between GUI and target engineers'''

    (CMD_SND, CMD_RCV) = range(0, 2)
    
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(VdCommCenter, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
            
        return cls._instance
    
    def __init__(self, passive_mode=False):
        '''
            Connstructor for VdCommCenter
            Create a queue to queue the message or command
            handler dictionary
        '''
        DebugLog.info_print("The communication center for VIOS Deployment Tool initialized.")
        self.handler_dict = {
                             "cmd_holder":['cmd_handler_hodler', 'cmd_callback_holder', 'data_holder'],
                             } 
        self.q_rcv_task = Queue.Queue(maxsize=100)
        self.q_snd_task = Queue.Queue(maxsize=100)
        self.delayed_snd_task = DelayedQueue(maxsize=10, delay_secs=60)
        self.msg_decoder = MsgCodec()
        
        self.passive_mode = passive_mode
        self.log_handler = None
        
    def __del__(self):
        self.stop()
        

 
    def _dispatchMsg(self, msg, cmd_direction, ):
        '''
        Search cmd in handler_dict, if hit call the handler or callback according to the cmd_director 
        '''
        cmd, _server_id, data = self.msg_decoder.decodeMsg(msg)
        if cmd in self.handler_dict.keys():
            #self.handler_dict[cmd][cmd_direction](msg)
            _handler_thrd = Thread(target=lambda msg=msg: self.handler_dict[cmd][cmd_direction](msg))
            _handler_thrd.start()
            
        if self.log_handler:
            self.log_handler.log_line("_Dispatch msg: %s " % msg )
            
    
    def start(self):
        '''
        Start the commnucation ceneter 
        '''
        DebugLog.info_print("In VdCommCenter Start process")
        self.start = True
        while self.start:
            DebugLog.debug_print_level2("in while ... ")
            if self.delayed_snd_task.available():
                self._dispatchMsg(self.delayed_snd_task.getMsg(), VdCommCenter.CMD_SND)
                
            if not self.q_snd_task.empty():
                DebugLog.debug_print_level1("_dispatch snd queue message")
                self._dispatchMsg(self.q_snd_task.get(), VdCommCenter.CMD_SND)
            
            if not self.q_rcv_task.empty():
                DebugLog.debug_print_level1("_dispatch rcv queue message")
                self._dispatchMsg(self.q_rcv_task.get(), VdCommCenter.CMD_RCV)
                
            if self.q_rcv_task.empty() and self.q_snd_task.empty():
                time.sleep(1)
                
    def poll_once(self):
        '''
        poll the commnucation ceneter every time there is new message is pushed in queue 
        '''
        DebugLog.debug_print_level1("In VdCommCenter poll once method")

        if self.delayed_snd_task.available():
            self._dispatchMsg(self.delayed_snd_task.getMsg(), VdCommCenter.CMD_SND)
              
        time.sleep(1)
        
        if not self.q_snd_task.empty():
            DebugLog.debug_print_level1("_dispatch snd queue message")
            self._dispatchMsg(self.q_snd_task.get(), VdCommCenter.CMD_SND)
            
        time.sleep(1)
        
        if not self.q_rcv_task.empty():
            DebugLog.debug_print_level1("_dispatch rcv queue message")
            self._dispatchMsg(self.q_rcv_task.get(), VdCommCenter.CMD_RCV)
            

    def stop(self):
        self.start = False
        
        
    def register_msg_handler(self, cmd, cmd_handler, callback):
        '''
        Register the command hanlder and callback
        '''
        cmd_value = [cmd_handler, callback]
        self.handler_dict[cmd] = cmd_value

    
    def sendMessage(self, msg):
        '''
        Add msg in the snd queue
        '''
        self.q_snd_task.put(msg)

        if self.passive_mode:
            self.poll_once()
        
        if self.log_handler:
            self.log_handler.log_line("Got msg: %s " % msg )
    
            
    def postMessage(self, msg):
        '''
        Add msg in the rcv queue
        '''
        self.q_rcv_task.put(msg)
        if self.passive_mode:
            self.poll_once()
        
        if self.log_handler:
            self.log_handler.log_line("Got response msg: %s " % msg )
            
    def add_log_handler(self, log_handler):
        '''add the message log_line handler'''
        self.log_handler = log_handler
    
    
    def sendDelayedMessage(self, msg):
        self.delayed_snd_task.putMsg(msg)
        