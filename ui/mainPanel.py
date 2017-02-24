#--*-- coding:utf-8 --*--
'''
Created on 2015��5��9��

@author: stm
'''

from Tkconstants import TOP
from ui.headerBar import HeaderBar
from ui.tablePanel import TablePanel
from ui.logPanel import LogPanel
from utils import DebugLog
from BasePanel import BasePanel

from base.msgcodec import MsgCodec
from base.cmdmsg import SERVERSCAN, GETSTATUS, CMDMsg
from ui.recordsPanel import RecordsPanel

class MainPanel(BasePanel):
    '''
    classdocs
    '''


    def createWidgets(self):      
       
        self.topPanel = HeaderBar(self)
        self.topPanel.pack(side=TOP)
        
        self.midPanel = TablePanel(self, self.appl, self.controller)
        self.midPanel.pack()
        
        self.recordPanel = RecordsPanel(self, self.appl, self.controller)
        self.recordPanel.pack_forget()
        
        #self.btmPanel = ProgressBar(self)
        #self.btmPanel.pack()
        
        #self.logPanel = LogPanel(self)
        #self.logPanel.pack()
    
    
    
    def __init__(self, parent, appl, controller):
        '''
        Constructor
        '''
        DebugLog.info_print("Construct main Panel")
        self.hide_show = True
        BasePanel.__init__(self, parent, appl, controller)
        self.pack()
        self.msg_decoder = MsgCodec()
        self.after(2000, self.updateUI)
        self.call_count = 0
        
    def updateUI(self):
        timer_update_default = 1000
        DebugLog.debug_print_level1("update UI in %d ms ... " % timer_update_default)
        server_data = self.controller.retrieve()
        
        if self.call_count % 30 == 0:
            self.controller.server_scan()
            self.call_count = 1
        self.call_count += 1

        self.midPanel.updateUI(server_data)
        self.after(timer_update_default, self.updateUI)
#         if CMDMsg.getCMD(SERVERSCAN) == cmd:
#             self.midPanel.updateUI(msg)
#         elif CMDMsg.getCMD(GETSTATUS) == cmd:
#             self.midPanel.updateUI(msg)


    def showHidePanel(self):
        
        if self.hide_show:
            self.midPanel.pack_forget()
            self.recordPanel.pack()
        else:
            self.recordPanel.pack_forget()
            self.midPanel.pack()
        self.hide_show = not self.hide_show
            
