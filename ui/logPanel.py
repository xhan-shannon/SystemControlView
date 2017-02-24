#--*-- coding:utf-8 --*--
'''
Created on 2015��5��9��

@author: stm
'''

from Tkinter import Frame, Button
import Tkinter
from Tkconstants import TOP, LEFT, RIGHT
from ui.scrolledList import ScrolledList
from utils import DebugLog
from base.logHandler import LogHandler

class LogPanel(Frame):
    '''
    classdocs
    '''


    def createWidgets(self):      
       
        self.listbox = ScrolledList(self, width=165)

        self.listbox.pack(side=TOP)        

    
    def __init__(self, parent):
        '''
        Constructor
        '''
        DebugLog.info_print("Construct Log Panel")
        self.frame = Frame.__init__(self, parent)
        self.pack()
        self.createWidgets()

    def getLogger(self):
        logger_inst = LogHandler(self.listbox)
        return logger_inst

        
        