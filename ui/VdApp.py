#--*-- coding:utf-8 --*--
'''
Created on 2015��5��8��

@author: stm
'''
from Tkinter import Frame
from ui.controllButtonsPanel import ControlButtonsPanel
from Tkconstants import LEFT, RIGHT, TOP, BOTTOM
from ui.mainPanel import MainPanel


class VdApp(Frame):
    '''
    classdocs
    ''' 
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(VdApp, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
            
        return cls._instance
       
    
    def __init__(self, master=None, controller=None, vd_config=None):
        '''
        Constructor, initialize the UI
        '''
        Frame.__init__(self, master)
        self.pack()
        
        self.vd_config = vd_config
        self.btnpanel = ControlButtonsPanel(master, self, controller)
        #self.btnpanel.pack(side=BOTTOM)
        self.setControlButtonsPanelVisible(False)
        self.mainpanel = MainPanel(master, self, controller)
        self.mainpanel.pack(side=TOP)


    def getSelectedItemsId(self):
        checked_id_list  = self.mainpanel.midPanel.getCheckedItemsIdList()
        return checked_id_list
            
    
    def getSelectedMachnineName(self):
        checked_names_list  = self.mainpanel.midPanel.getCheckedNamesList()
        return checked_names_list
    
    def getSelectedMachnineIP(self):
        checked_ip_list  = self.mainpanel.midPanel.getCheckedIPList()
        return checked_ip_list
    
    
    def getMainPanel(self):
        return self.mainpanel
    
    def getControlButtonsPanel(self):
        return self.btnpanel
    
    def setControlButtonsPanelVisible(self, visible):
        if visible:
            self.btnpanel.pack(side=BOTTOM)
        else:
            self.btnpanel.forget()
        
