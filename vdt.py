#coding:utf-8
'''
Created on 2015��5��8��

@author: stm
'''



from threading import Thread
import time


from Tkinter import Tk, Button
from base.vdcommcnt import VdCommCenter
from utils import DebugLog
from engine.helloeng import HelloEng
from ui.VdApp import VdApp
import ConfigParser
import os
from utils.ErrorHandler import ConfigFileError
from controller.SvrController import SvrController
from model.dataentity import DataEntity

DebugLog.init_log(True, True)
DebugLog.loglevel1 = True

vdCommCenter_inst = VdCommCenter(passive_mode=False)
appl = None


def hello_callback(param):
    DebugLog.debug_print_level1("in hello callback")
    if isinstance(param, list):
        print param[0]


def hello_dealer(param):
    DebugLog.debug_print_level1("in hello dealer")
    if isinstance(param, list):
        print param[0]
    else:
        print param
    


def clean_know_hosts():
    '''Clean ssh known_hosts'''
    known_hosts_file = "/root/.ssh/known_hosts"
    if os.path.isfile(known_hosts_file):
        os.system("echo '' > %s" % known_hosts_file)


if __name__ == '__main__':

    
    try:
        # Test exception throw
        #raise Exception, "Test exception catchup ... "
        
        clean_know_hosts()
        
        vd_config = ConfigParser.ConfigParser()
        vd_config_fname = 'vd.cfg'
        DebugLog.debug_print_level2("The config_file is " + vd_config_fname)
        
        if vd_config and os.path.exists(vd_config_fname):
            vd_config.read(vd_config_fname)
        else:
            raise ConfigFileError('%s not found' % (vd_config_fname))
        
        vdCommCenterThrd = Thread(target=vdCommCenter_inst.start)
        vdCommCenterThrd.start()
        
        server_data_entity = DataEntity(vd_config) 
        
        vd_contr = SvrController(vd_config, vdCommCenter_inst, server_data_entity)
            
        
        root = Tk()
        root.title("VIOS Deploy Tool")
        DebugLog.info_print("Create Vd App")

        appl = VdApp(root, vd_contr, vd_config)
        #root.maxsize(1112, 676)
        root.protocol('WM_DELETE_WINDOW',None)
        root.mainloop()

        vdCommCenter_inst.stop()
        root.quit()
    except :
        DebugLog.exception_print("Catch exception")
        
