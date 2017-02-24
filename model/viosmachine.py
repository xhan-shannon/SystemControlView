#--*-- coding:utf-8 --*--
'''
Created on 2015��5��12��

@author: stm
'''

import json
from base.cmdmsg import CMD_MSGS, CMDMsg

FIELD_NAME = ["AUTO_FLAG",
              "SELECTION",
              "INDEX",
              "SERVERIPHMC",
#              "SERVERPORTSWITCH",
              "SERVER_SN",
              "PHASE",
              "PROGRESS",
              "SERVER_NAME",
              "IP_FOR_NIMINSTALL",
              "IP_GW_FOR_NIMINSTALL",
              ]
DATA_COLS = len(FIELD_NAME)
#AUTO_FLAG, SEL_ID, IDX_ID, IP_ID, PORT_ID, SN_ID, \
AUTO_FLAG, SEL_ID, IDX_ID, IP_ID, SN_ID, \
PHASE, PROGRESS, NAME_ID, \
IP_FOR_NIMINSTALL, IP_GW_FOR_NIMINSTALL = range(DATA_COLS)

class VIOSMachineRecord(object):
    '''
    Represent the vios machine and its status
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.name = ""
        self.contr_ip = ""
        self.serial_nm = ""
        self.portatnm = ""
        self.state = ""
        self.enabled = False
        self.indx = 0
        self.deployprgress = ""
        self.ip_for_niminstall = ""
        self.ip_gw_for_niminstall = ""
        
    def setServerName(self, name):
        self.name = name
        
    def setChecked(self, val):
        self.enabled = val
    
    def setContrIP(self, ip):
        self.contr_ip = ip
        
    def setSerialNm(self, sn):
        self.serial_nm = sn
        
    def setPortAtNm(self, port):
        self.portatnm = port
    
    def setState(self, state):
        self.state = state
        
    def setIndex(self, idx):
        self.indx = idx
        
    
    def setIPForNimInstall(self, ip_for_niminstall):
        self.ip_for_niminstall = ip_for_niminstall
        
    def setIPGwForNimInstall(self, ip_gw_for_niminstall):
        self.ip_gw_for_niminstall = ip_gw_for_niminstall
        
        
    def getServerName(self):
        return self.name 
    
    def getContrIP(self):
        return self.contr_ip
        
    def getSerialNm(self):
        return self.serial_nm
        
    def getPortAtNm(self):
        return self.portatnm
    
    def getState(self):
        return self.state
    
    def getDeployProgress(self):
        return self.deployprgress
    
    def getIndex(self):
        return self.indx
    
    def getCheckStatus(self):
        return self.enabled
    
    
    def getIPGwForNimInstall(self):
        return self.ip_gw_for_niminstall
    
    
    def getIPForNimInstall(self):
        return self.ip_for_niminstall
        
    
    def getValueById(self, idx):
        val = None
        if SEL_ID == idx:
            val = self.getCheckStatus()
        elif IDX_ID == idx:
            val = self.getIndex()
        elif IP_ID == idx:
            val = self.getContrIP()
        elif SN_ID == idx:
            val = self.getSerialNm()
        elif PHASE == idx:
            val = self.getState()
        elif NAME_ID ==idx:
            val = self.getServerName()
        elif PROGRESS == idx:
            val = self.getDeployProgress()    
        elif IP_FOR_NIMINSTALL == idx:
            val = self.getIPForNimInstall()
        elif IP_GW_FOR_NIMINSTALL == idx:
            val = self.getIPGwForNimInstall()    
            
        return val 
    

    
    
    def getContrIPDesc(self):
        return self.contr_ip.__str__()
    
    
    def getNameDesc(self):
        return self.name.__str__()
    
    
    def getSerialNmDesc(self):
        pass
    
    
    def retrieveValues(self):
        '''
        format vios_machine_information data as json string
        '''
        idkey =  'machine_' + self.getIndex()

        json_str_dict = {}
        json_str_dict[idkey] = self.getIndex()
        json_str_dict[self.getContrIPDesc()] = self.getContrIP()
        json_str_dict[self.getNameDesc()] = self.getServerName()
        json_str_dict[self.getSerialNmDesc()] = self.getSerialNm()
        json_str_dict[self.getStateDesc()] = self.getState()
        
        #return json.du


    def setDeployProgress(self, deploy_progess):
        self.deployprgress = deploy_progess
    
    
    def updateValue(self, idx, val):
        if SEL_ID == idx:
            self.setChecked(val)
        elif IDX_ID == idx:
            self.setIndex(val)
        elif IP_ID == idx:
            self.setContrIP(val)
        elif SN_ID == idx:
            self.setSerialNm(val)
        elif PHASE == idx:
            self.setState(val)
        elif PROGRESS == idx:
            self.setDeployProgress(val)
        elif NAME_ID ==idx:
            self.setServerName(val)
        elif IP_FOR_NIMINSTALL == idx:
            self.setIPForNimInstall(val)
        elif IP_GW_FOR_NIMINSTALL == idx:
            self.setIPGwForNimInstall(val)    
            
        
        
        
    def get_stage_id_val(self):
        stage_str = self.getDeployProgress()
        id_val = -1
        for idx in range(len(CMD_MSGS)):
            if CMDMsg.getCmdDesc(idx) == stage_str:
                id_val = idx
                break;
        
        return id_val
    
        
    
        
    
    
        
    
        
        