#--*-- coding:utf-8 --*--
'''
Created on 2015��5��8��

@author: stm
'''
from base.engine import EngineBase
from utils import DebugLog


class HelloEng(EngineBase):
    '''
    classdocs
    '''
    def __init__(self):
        pass
    
    def hello_dealer(self, msg):
        DebugLog.info_print("Got the command tranfering")
        pass