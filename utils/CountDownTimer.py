#--*-- coding:utf-8 --*--
'''
Created on 2015��5��11��

@author: stm
'''
import threading
import DebugLog
import time

ONCE, LOOP = range(2)

class CountDownTimer(object):
    '''
    classdocs
    '''


    def callself(self):
        DebugLog.debug_print_level2("in 'callself func of CountDownTimer")
        
        while self.running:
            self.action()
            time.sleep(1)
#             if LOOP == self.mode:
#                 DebugLog.debug_print_level2("in 'callself func of CountDownTimer: start another thread to call self")
#                 thrd = threading.Timer(self.cnt, self.callself)
#                 thrd.start()
        
    
    def __init__(self, cnt, action, mode=ONCE):
        '''
        Constructor
        '''
        self.action = action
        self.mode = mode
        self.cnt = cnt
        self.running = True
    

    def __del__(self):
        self.running = False
    
    def start(self):
        DebugLog.debug_print_level1("in 'callself func of CountDownTimer: start thread to call self")
        thrd = threading.Timer(self.cnt, self.callself)
        thrd.start()
        
    def stop(self):
        self.running = False
    
    
        