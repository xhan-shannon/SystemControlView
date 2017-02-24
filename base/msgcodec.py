#--*-- coding:utf-8 --*--
'''
Created on 2015��5��12��

@author: stm
'''
import string

class MsgCodec(object):
    '''
    Codec msg 
    Encode as CMD: Server_id, Param1, Param2, ...
    Decode as msg=CMD, data=Params 
    '''
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(MsgCodec, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
            
        return cls._instance

    def __init__(self):
        '''
        Constructor
        '''
        
    def decodeMsg(self, msg):
        '''
        The command or command response format is as below
        "cmd: server_id, param1, param2,..."
        "cmd: server_id, response1, ...."
        @msg: 
        $return value: cmd, data  
        '''
        if isinstance(msg, list):
            msg_str = msg.join()
        else:
            msg_str = msg
            
        cmd, data = string.split(msg_str, ":", 1)
        data_id, data = string.split(data, ",", 1)
        return cmd, data_id, data
    
    def encodeMsg(self, cmd, server_id, *data):
        '''
        encode the msg as CMD: Server_id, Param1, Param2, ....
        Params are from data list
        '''
        params = ""
        try:
            if isinstance(data[0], list):
                #for param in data:
                #    params = param + ","
                params = str(data[0])
        except:
            params = ""
        msg_str = cmd + ":" + str(server_id) + "," + params
        return msg_str