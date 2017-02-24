#--*-- coding:utf-8 --*--
'''
Created on 2015��7��22��

@author: stm
'''
from Queue import Queue
import time

class DelayedQueue(Queue):
    '''
    The delayed queue is used to send messages after a delayed time
    '''
    def __init__(self, maxsize, delay_secs):
        Queue.__init__(self, maxsize)
        self.timestamp = None
        self.counttime = delay_secs

    def putMsg(self, msg):
        self.put(msg)
    
    
    def available(self):
        bAval = False
        
        btime_elapsed = False
        if not self.timestamp:
            btime_elapsed = True
            
            
        if self.timestamp:
            cur_time = time.time()
            elapsed_time = cur_time - self.timestamp
            if elapsed_time > self.counttime:
                btime_elapsed = True
                
        if self.empty():
            if self.timestamp:
                self.timestamp = None
            bAval = False
        else:
            bAval = True
            
        bAval = btime_elapsed and bAval
                
        return bAval
    
    
    def getMsg(self):
        itm = None
        if self.available():
            itm = self.get()
            self.timestamp = time.time()


        return itm
        
        