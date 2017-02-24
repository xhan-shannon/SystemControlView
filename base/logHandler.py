#--*-- coding:utf-8 --*--
'''
Created on 2015��5��11��

@author: stm
'''

class LogHandler(object):
    '''
    classdocs
    '''


    def __init__(self, logger_handler):
        '''
        Constructor
        '''
        self.logger = logger_handler
        
    def log_line(self, msg):
        if self.logger:
            self.logger.log_line(msg)
    
        
        
        