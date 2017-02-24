#--*-- coding:utf-8 --*--
'''
Created on 2015��5��10��

@author: stm
'''
from Tkinter import Frame, Scrollbar, Listbox
from Tkconstants import BOTH, YES, SUNKEN, RIGHT, Y, LEFT, END

class ScrolledList(Frame):
    '''
    a customizable scrolled listbox compoent
    '''


    def makeWidgets(self, width):
        scrbar_width = 30 
        scrbar = Scrollbar(self, width=scrbar_width)
        self.list = Listbox(self, relief=SUNKEN, width=width-30)
        scrbar.config(command=self.list.yview)
        self.list.config(yscrollcommand=scrbar.set)
        scrbar.pack(side=RIGHT, fill=Y)
        self.list.pack(side=LEFT, expand=YES, fill=BOTH)
        
        
    
    
    def __init__(self, parent, width):
        '''
        Constructor
        '''
        Frame.__init__(self, parent)
        self.pack(expand=YES, fill=BOTH)
        self.makeWidgets(width)
        
    def log_line(self, msg):
        self.list.insert(END, msg)
#         if self.list.size():
#             self.list.insert(1, msg)
#         else:
#             self.list.insert(END, msg)
#         
        