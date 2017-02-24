#--*-- coding:utf-8 --*--
'''
Created on 2015��5��9��

@author: stm
'''
from utils import DebugLog
from ui.BasePanel import BasePanel
from Tkinter import Label, StringVar, Checkbutton, Button
from Tkconstants import SUNKEN, RIDGE
from base.cmdmsg import CHECK_ENABLED, SAVESELECTION, CMDMsg, UPDATEPASSWD,\
    AUTOSTART, INSTALL_VIOS_ONLY
from model.viosmachine import NAME_ID, IP_ID
from base.msgcodec import MsgCodec
from base.CustomedButton import CustomedButton



#record_items = ["OneClick", "Selection", "ID", "IP", "Port", "SN", "Phase", "Progress"]
#items_width = [25, 10, 5, 25, 5, 15, 35, 35]
#(FULL_INSTALL, SEL_N, ID_N, IP_N, PORT_N, SN_N, PHASE_N, PROGRESS_N) = range(len(record_items))

record_items = ["Full Install with PD", "Install VIOS", "ID", "IP", "SN", "Phase", "Progress"]
items_width = [15, 10, 5, 25, 15, 35, 35]
(FULL_INSTALL, ONLY_INSTALL_VIOS, ID_N, IP_N, SN_N, PHASE_N, PROGRESS_N) = range(len(record_items))


class TablePanel(BasePanel):
    '''
    Display the machine related properties, such as IP, SN and the status of installation
    '''


    def __init__(self, parent, appl, controller):
        '''
        Constructor
        '''
        DebugLog.info_print("Construct table Buttons Panel")
        self.mtrx = []
        self.oneclickbtns = []
        self.only_install_vios_btns = []
        BasePanel.__init__(self, parent, appl, controller)
        self.pack()
        self.msgcoder = MsgCodec()
        self.setdefaultvalues()

    
    def sendMsg(self, server_id, msg_type_id, bStop=False):
        DebugLog.info_print("Send Msg via button click with server_id: %d" % server_id)
        #server_data = self.getServerData(server_id)
        
        params = [server_id, bStop]
        msg = self.msgcoder.encodeMsg(CMDMsg.getCMD(msg_type_id), server_id, params)
        self.controller._sendMsg2CommCnt(msg)

    
    def disable_part_install_btn(self, idx):
        btn = self.only_install_vios_btns[idx]
        btn.set_as_disabled()
    
    
    def full_install_handler(self, server_id, bStop=False):
        self.sendMsg(server_id, AUTOSTART, bStop)
        self.disable_part_install_btn(server_id)
        
        
    def disable_full_install_btn(self, idx):
        btn = self.oneclickbtns[idx]
        btn.set_as_disabled()
    
    
    def only_install_vios_handler(self, server_id, bStop=False):
        self.sendMsg(server_id, INSTALL_VIOS_ONLY, bStop)
        self.disable_full_install_btn(server_id)
    
    def createWidgets(self):   
        col = 0   
        idx = 0
        for itm in record_items:
            lbl = Label(self, text=itm, relief=RIDGE, width=items_width[idx], height=2)
            lbl.grid(row=0, column=col)
            col += 1
            idx += 1


        self.checkVar = [] 
        
        for rowidx in range(10):
            row_list = []
            for colidx in range(len(record_items)):
                if FULL_INSTALL == colidx:
                    btn = CustomedButton(self,
                                       server_id=rowidx,
                                       handler=self.full_install_handler,
                                       text=record_items[colidx],
                                       height=1,
                                       width=items_width[colidx])
                    self.oneclickbtns.append(btn)
                    btn.update_state(False)
                    btn.update()
                    row_list.insert(colidx, btn)
                    
                elif ONLY_INSTALL_VIOS == colidx:
                    btn = CustomedButton(self,
                                       server_id=rowidx,
                                       handler=self.only_install_vios_handler,
                                       text=record_items[colidx],
                                       height=1,
                                       width=items_width[colidx])
                    self.only_install_vios_btns.append(btn)
                    btn.update_state(False)
                    btn.update()
                    row_list.insert(colidx, btn)
#                 elif SEL_N == colidx:
#                     self.checkVar.append(StringVar())
#                     row_list.insert(colidx, Checkbutton(self, 
#                                                         variable=self.checkVar[rowidx],
#                                                         onvalue = "1",
#                                                         offvalue = "0",
#                                                         relief=SUNKEN, 
#                                                         command = self.saveCheckStatus,
#                                                         width=items_width[colidx]-3))
                else:
                    row_list.insert(colidx,Label(self, relief=SUNKEN, width=items_width[colidx]))
                row_list[colidx].grid(row=rowidx+1, column=colidx)
            self.mtrx.append(row_list)
 
    
        
    def setdefaultvalues(self):
        for rowidx in range(len(self.mtrx)):
            #self.mtrx[rowidx][SEL_N].deselect()
            pass
    
    
    def updateUI(self, data):
        DebugLog.debug_print_level1("in tablePanel updateUI method")
        
        DebugLog.debug_print_level1(str(data))
        
        col_max = len(self.mtrx[0])
        for rowidx in range(len(self.mtrx)):
            for colidx in range(ID_N, col_max):
                if ID_N == colidx:
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
    

        
        