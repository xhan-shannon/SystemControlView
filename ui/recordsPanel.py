#--*-- coding:utf-8 --*--
'''
Created on 2015��5��9��

@author: stm
'''
from utils import DebugLog
from ui.BasePanel import BasePanel
from Tkinter import Label, StringVar, Checkbutton, Button, Text
from Tkconstants import SUNKEN, RIDGE, TOP
from base.cmdmsg import CHECK_ENABLED, SAVESELECTION, CMDMsg
from model.viosmachine import NAME_ID, IP_ID
from base.msgcodec import MsgCodec



class RecordsPanel(BasePanel):
    '''
    Display the machine related properties, such as IP, SN and the status of installation
    '''


    def __init__(self, parent, appl, controller):
        '''
        Constructor
        '''
        DebugLog.info_print("Construct records Panel")
        self.mtrx = []
        BasePanel.__init__(self, parent, appl, controller)
        self.pack()
        self.msgcoder = MsgCodec()
        self.setdefaultvalues()

    
    def backtomainPanel(self):
        self.appl.getMainPanel().showHidePanel()
        self.appl.getControlButtonsPanel().pack()
    
    
    def createWidgets(self):   
        col = 0   
        idx = 0

        textbox = Text(self, relief=RIDGE, width=160, height=38)
        btnret = Button(self, text="Return",command=self.backtomainPanel)
        
        textbox.pack(side=TOP)
        btnret.pack(side=TOP)



 
    
        
    def setdefaultvalues(self):
        for rowidx in range(len(self.mtrx)):
            #self.mtrx[rowidx][SEL_N].deselect()
            pass
    
    
    def updateUI(self, data):
        DebugLog.info_print("in tablePanel updateUI method")
        
#         if CMDMsg.getCMD(SERVERSCAN) == cmd:
#             self.updateAndSaveData(body)
#         elif CMDMsg.getCMD(GETSTATUS) == cmd:
#             self.updateAndSaveDataByName(body)
        DebugLog.info_print(str(data))
        
        col_max = len(self.mtrx[0])
        for rowidx in range(len(self.mtrx)):
            for colidx in range(col_max):
                if SEL_N == colidx:
                    pass
                elif ID_N == colidx:
                    id_val = data[rowidx][colidx]
                    idx = int(id_val) + 1
                    self.mtrx[rowidx][colidx].config(text=str(idx))
                else:
                    self.mtrx[rowidx][colidx].config(text=data[rowidx][colidx])


    def getCheckedItemsIdList(self):
        checked_items_list = []
        for indx in range(len(self.mtrx)):
            #if self.mtrx[idx][0].variable.get():
            checkStatus = self.checkVar[indx].get()
            DebugLog.debug_print_level1("Get the select status : %s" % checkStatus)
            if CHECK_ENABLED == checkStatus:
                checked_items_list.append(indx)
        
        return checked_items_list                    
                    
    def getCheckedNamesList(self):
        return self._getCheckedItemsList(NAME_ID)


    def getCheckedIPList(self):
        return self._getCheckedItemsList(IP_ID)

    
    def _getCheckedItemsList(self, indx):
        checked_items_list = []
        for idx in range(len(self.mtrx)):
            #if self.mtrx[idx][0].variable.get():
            checkStatus = self.checkVar[idx].get()
            DebugLog.debug_print_level1("Get the select status : %s" % checkStatus)
            if CHECK_ENABLED == checkStatus:
                checked_items_list.append(self.machine_records[idx].getValueById(indx))
        
        return checked_items_list
                
        
    def saveCheckStatus(self):
        checked_items_list = []
        for indx in range(len(self.mtrx)):
            #if self.mtrx[idx][0].variable.get():
            checkStatus = self.checkVar[indx].get()
            DebugLog.debug_print_level1("Get the select status : %s" % checkStatus)
            data_val = self.msgcoder.encodeMsg(CMDMsg.getCMD(SAVESELECTION), indx, list(checkStatus)) 
            
            self.controller.updateData(data_val)
            
        
        return checked_items_list     
    

        
        