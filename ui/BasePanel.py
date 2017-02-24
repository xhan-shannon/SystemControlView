#--*-- coding:utf-8 --*--
'''
Created on 2015��5��11��

@author: stm
'''
from Tkinter import Frame
from abc import abstractmethod

class BasePanel(Frame):
    '''
    classdocs
    '''

    def __init__(self, parent, appl, controller):
        '''
        Constructor
        '''
        self.controller = controller
        self.appl = appl
        self.frame = Frame.__init__(self, parent)
        self.pack()
        self.createWidgets()
        
        
    @abstractmethod
    def updateUI(self, msg):
        pass