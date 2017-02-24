#!/usr/bin/python
# -*-coding: utf-8 -*-
'''
Created on 

@author: stm
'''
import logging
import os

PD_DEBUG_LOG = True

DEBUG_LOG_PRINT = True

PD_LOG_LEVEL_DEBUG, PD_LOG_LEVEL_INFO, PD_LOG_LEVEL_WARNING = range(3)

PD_LOG_LEVEL = PD_LOG_LEVEL_INFO

CMD_SEP = '-'*100

is_verbose = False
loglevel1 = False
loglevel2 = False

debug_logger = None
info_logger = None
infolvl_handler = None
debuglvl_handler = None
err_logger = None
errlvl_handler = None


def init_log(full=False, logfile=False):
    if full:
        logging.basicConfig(format='[%(pathname)s: %(lineno)d: %(levelname)s:%(asctime)s]:%(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S', 
                        level=logging.DEBUG)
        logging.getLogger("paramiko").setLevel(logging.DEBUG)
    else:
        logging.basicConfig(format='%(message)s', level=logging.INFO)
        logging.getLogger("paramiko").setLevel(logging.WARN)
    
    if logfile:
        log_dir_name = "log"
        if not os.path.exists(log_dir_name):
            os.mkdir(log_dir_name)
            
        global debug_logger
        global info_logger
        global infolvl_handler
        global debuglvl_handler
        
        debuglog_file = os.path.join(log_dir_name, "debug.log")
        debuglvl_handler = logging.FileHandler(debuglog_file, "w")
        fmt = logging.Formatter('[%(levelname)s:%(asctime)s]:%(message)s')
        debuglvl_handler.setFormatter(fmt)
        debuglvl_handler.createLock()
        
        #%(funcName)s
        debug_logger = logging.getLogger("debug_logger")
        debug_logger.addHandler(debuglvl_handler)
        debug_logger.setLevel(logging.DEBUG)

        
        infolog_file = os.path.join(log_dir_name, "info.log")
        infolvl_handler = logging.FileHandler(infolog_file, "w")
        fmt = logging.Formatter('[%(asctime)s]:%(message)s')
        infolvl_handler.setFormatter(fmt)
        infolvl_handler.setLevel(logging.INFO)
        infolvl_handler.createLock()
        
        info_logger = logging.getLogger("info_logger")
        info_logger.addHandler(infolvl_handler)
        info_logger.setLevel(logging.INFO)
        
        global err_logger
        global errlvl_handler
        errlog_file = os.path.join(log_dir_name, "error.log")
        errlvl_handler = logging.FileHandler(errlog_file, "w")
        fmt = logging.Formatter('[%(levelname)s:%(asctime)s]:%(message)s')
        errlvl_handler.setFormatter(fmt)
        errlvl_handler.createLock()
        
        #%(funcName)s
        err_logger = logging.getLogger("error_logger")
        err_logger.addHandler(errlvl_handler)
        err_logger.setLevel(logging.ERROR)
        
        handlers = logging.root.handlers
        for hdlr in handlers:
            logging.root.removeHandler(hdlr)
        #logging.root.addHandler(debuglvl_handler)
        


    
def exception_print(msg):
    '''print exception '''
    errlvl_handler.acquire()
    err_logger.exception(msg)
    errlvl_handler.release()
    
        
def debug_print(msg, level):
    '''print the debug information'''
    dbgmsg = '[DBG L%d]| %s' %(level, msg)
    debuglvl_handler.acquire()
    debug_logger.debug(dbgmsg)
    debuglvl_handler.release()


def debug_print_level1(msg):
    if loglevel1:
        debug_print(msg, 1)
    else:
        pass

def debug_print_level2(msg):
    if loglevel2:
        debug_print(msg, 2)
    else:
        pass
    
    
def info_print(msg):
    infolvl_handler.acquire()
    info_logger.info("| " + msg)
    infolvl_handler.release()
    

# import sys
# 
# def info(etype, value, tb):
#     if hasattr(sys, 'ps1') or not sys.stderr.isatty():
#     # we are in interactive mode or we don't have a tty-like
#     # device, so we call the default hook
#         sys.__excepthook__(etype, value, tb)
#     else:
#         import traceback, pdb
#         # we are NOT in interactive mode, print the exception…
#         traceback.print_exception(etype, value, tb)
#         print
#         # …then start the debugger in post-mortem mode.
#         # pdb.pm() # deprecated
#         pdb.post_mortem(tb) # more “modern”
# 
# sys.excepthook = info

class Messages(object):
    '''Define the common messages'''
    STEP_INFO = u"检查点："