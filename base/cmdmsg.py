#--*-- coding:utf-8 --*--
'''
Created on 2015��5��12��

@author: stm
'''

CMD_MSGS = [("SERVERSCAN", "Server SCAN", "Step 1"),
            #("ADDTOHMC", "Add To HMC"),
            ("UPDATEPASSWD", "Update Password"),
            ("CHECKUPDATEPASSWD", "check update password"),
            ("RECOVERPROFILE", "Recover profile"),
            ("CHECKRECOVERPROFILE", "check recover profile"),
            ("POWERONSERVER", "Power on the server"),
            ("CHECKPOWERONSERVER", "check power on server"),
#             ("GETSERVERSLOTS", "Get Server Slots"),
            ("CREATEVIOSLPAR", "Create VIOS Lpar"),
            ("CHECKCREATEVIOSLPAR", "Check Create VIOS Lpar"),
            ("PREPAREHOSTSFILE", "Modify hosts file"),
            ("CHECKHOSTSFILE", "Check hosts file"),
            ("DEFINESERVER", "Define server in nim"),
            ("CHECKDEFINEDSERVER", "Check defined server in nim"),
            ("ASSIGNRESOURCE", "Assign installation resource"),
            ("CHECKASSIGNEDRES", "Check Assigned resource"),
            ("INSTALLVIOS", "Install VIOS"),
            ("CHECKVIOSINSTALL", "Check VIOS Installation"),
            ("CLEANNIMRESOURCE","Clean NIM Define"),
            ("CHECKCLEANSTATUS", "Check clean nim resource"), 
            ("ACCEPTLICENSE", "Accept License"),
            ("CHECKACCEPTLICENSE", "Check Accept License status"),
            ("SETDEFAULTIP", "Set default IP"),
            ("POWEROFFSERVER", "Power off Server"),
            ("CHECKPOWEROFFSERVER", "check power off server"),
            ("REMVSERVER", "Remove Server From HMC"),
            ("CHECKREMVSERVER", "check remove server from HMC"),
            ("RST_FW_FCTRY", "Reset firmware factory settings"),
            ("CHECKRST_FW_FCTRY", "check reset firmware factory setting"),
            ("RMV_NON_HMC", "Remove non-HMC connections"),
            ("CHECKRMV_NON_HMC", "check remove no-HMC connections"),
            ("ASM_POWERON", "Asm power on"),
            ("CHECKASM_POWERON", "check asm power on"),
            
            #("HMCTOIVM", "Convert HMC to IVM"),
            ("INSTALLSW", "Install Software"),
            ("SETDEFAULTIPANDSHUTDOWN", "Set default IP and shutdown server"),
            ("GETSTATUS", "Get Current Status"),
            ("SHOWRECORDS", "Show Records"),
            ("SAVESELECTION", "Save Selections"),
            ("UPDATESTATUS", "Update Status"),
            ("AUTOSTART", "Auto Start Deployment"),
            ("INSTALLVIOSONLY", "Only Install VIOS"),
            ]

CMD_NAME_IDX = 0
CMD_DESC_IDX = 1
           
(SERVERSCAN, UPDATEPASSWD, CHECKUPDATEPASSWD, \
 RECOVERPROFILE, CHECKRECOVERPROFILE, \
 POWERONSERVER, CHECKPOWERONSERVER, \
 CREATEVIOSLPAR, CHECKCREATEVIOSLPAR, \
 PREPAREHOSTSFILE, CHECKHOSTSFILE, \
 DEFINESERVER, CHECKDEFINEDSERVER, \
 ASSIGNRESOURCE, CHECKASSIGNEDRESOURCE, \
 INSTALLVIOS, CHECKVIOSINSTALL, \
 CLEANNIMRESOURCE, CHECKCLEANSTATUS, \
 ACCEPTLICENSE, CHECKACCEPTLICENSE, \
 SET_DEFAULT_IP, \
 POWEROFFSERVER, CHECKPOWEROFFSERVER, \
 REMVSERVER, CHECKREMVSERVER, \
 RST_FW_FCTRY, CHECKRST_FW_FCTRY, \
 RMV_NON_HMC, CHECKRMV_NON_HMC,  ASM_POWERON, CHECKASM_POWERON, \
 INSTALLSW, SET_DEFAULT_IP_AND_SHUTDOWN, GETSTATUS, SHOWRECORDS, \
 SAVESELECTION, UPDATESTATUS, AUTOSTART, INSTALL_VIOS_ONLY) = range(len(CMD_MSGS))  

CHECK_ENABLED="1"
CHECK_DISABLED="0"

class CMDMsg(object):
    '''
    classdocs
    '''
    def __init__(self):
        pass
    
    @staticmethod
    def getCMD(idx):
        return CMD_MSGS[idx][0]
    
    @staticmethod
    def getCmdDesc(idx):
        return CMD_MSGS[idx][1]

        