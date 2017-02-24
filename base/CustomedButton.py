#--*-- coding:utf-8 --*--
'''
Created on 2015年6月1日

@author: stm
'''
from Tkinter import Button
from utils import DebugLog

class CustomedButton(Button):
    '''
    The button bound with id which represents the server id
    '''

    
    def __init__(self, parent=None, server_id=0, handler=[], **kw):
        '''
        Constructor
        '''
        self.server_id = server_id
        self.start = False
        Button.__init__(self, parent, kw)
        self.func = handler
        #(lambda sid=self.server_id: handler(sid))
        
        self.config(command=self.switch_state_and_exec)


    def switch_state(self):
        self.start = not self.start
        self.update_text()


    def restore_to_enabled(self):
        self.config(state="active")
    
    
    def set_as_disabled(self):
        self.config(state="disabled")
        
        
    def switch_state_and_exec(self):
        self.switch_state()
        bStop = False
        if self.start:
            #pass
            self.func(self.server_id, bStop)
        else:
            #pass
            bStop = True
            self.func(self.server_id, bStop)
        self.config(state="disabled")
        self.after(1000, self.restore_to_enabled)
        
    def update_text(self):
        if not self.start:
            self.config(text="Start -->>--")
        else:
            self.config(text="Start --||--")
    
    def update_state(self, bState):
        self.start = bState
        self.update_text()