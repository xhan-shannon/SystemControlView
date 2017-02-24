#--*-- coding:utf-8 --*--
'''
Created on 2015��5��9��

@author: stm
'''

from Tkinter import Frame, Button
import Tkinter
from Tkconstants import TOP, LEFT, RIGHT
from ttk import Progressbar
from utils import DebugLog

class ProgressBar(Frame):
    '''
    classdocs
    '''


    def createWidgets(self):      
       
        first_row = Progressbar(self)
               
        first_row.pack(side=TOP)

    
    def __init__(self, parent):
        '''
        Constructor
        '''
        DebugLog.info_print("Construct ProgressBar Panel")
        self.frame = Frame.__init__(self, parent)
        self.pack()
        self.createWidgets()


        
        