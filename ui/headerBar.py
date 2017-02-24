#--*-- coding:utf-8 --*--
'''
Created on 2015��5��9��

@author: stm
'''

from Tkinter import Frame, Button, Label
import Tkinter
from Tkconstants import TOP, LEFT, RIGHT
import time

from utils import DebugLog
from utils.CountDownTimer import CountDownTimer
from version import VERSION_NUM


class HeaderBar(Frame):
    '''
    Show Current status and date time in header bar
    '''   
    
    def createWidgets(self):
        lbl_font = ('times', 18, 'bold')      
       
#         Tkinter.Label(self, text="CURRENT STATUS: ", font=lbl_font,
#                       width=20, height=3).pack(side=LEFT)
#         
        self.current_status_lbl = Label(self, text="Version: %s" % VERSION_NUM, 
                                        font=lbl_font, width=30)
        self.current_status_lbl.pack(side=LEFT)
#         expnd_clps_btn          = Button(self, text="Collapse",
#                                          width=27, height=2)
#         expnd_clps_btn.pack(side=LEFT)
#         expnd_clps_btn.config(command=self.showhidebtns)
        
        timestr = time.asctime()
        self.current_datetime_lbl = Tkinter.Label(self, text=timestr, 
                                                  font=lbl_font, width=50)
        self.current_datetime_lbl.pack(side=RIGHT)
       
    
    
    def updateTimestamp(self):
        timestr = time.asctime()
        if self.current_datetime_lbl:
            self.current_datetime_lbl.config(text=timestr)
            self.current_datetime_lbl.after(300, self.updateTimestamp)
    
                
        
    def startTimer(self):
        #self.timer1 = self.CountDownTimer(1, self.updateTimestamp, 1)
        #self.timer1.start()
        self.current_datetime_lbl.after(300, self.updateTimestamp)
        
    
    
    def __init__(self, parent):
        '''
        Constructor
        '''
        DebugLog.info_print("Construct headBar Panel")
        Frame.__init__(self, parent)
        self.pack()
        self.createWidgets()
        
        self.startTimer()
        
    def __del__(self):
        self.timer1.stop()
        
    
    def showhidebtns(self):
        pass
