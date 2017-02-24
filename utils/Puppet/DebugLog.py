#!/usr/bin/python
# -*-coding: utf-8 -*-
'''
Created on 

@author: stm
'''
import logging

PD_DEBUG_LOG = True

DEBUG_LOG_PRINT = True

PD_LOG_LEVEL_DEBUG, PD_LOG_LEVEL_INFO, PD_LOG_LEVEL_WARNING = range(3)

PD_LOG_LEVEL = PD_LOG_LEVEL_INFO

CMD_SEP = '-'*100

is_verbose = False
loglevel1 = False
loglevel2 = False

def init_log(full=False):
    if full:
        logging.basicConfig(format='[%(pathname)s: %(lineno)d: %(levelname)s:%(asctime)s]:%(message)s', 
                        level=logging.DEBUG)
        logging.getLogger("paramiko").setLevel(logging.DEBUG)
    else:
        logging.basicConfig(format='%(message)s', level=logging.INFO)
        logging.getLogger("paramiko").setLevel(logging.WARN)


def pd_log(loglevel, details):
    pass


def stepinfo(info):
    logging.info(Messages.STEP_INFO + info)    # "Step info: " 


def stepinfo_idx(info, id):
    logging.info(Messages.STEP_INFO + " %d:" % id + info) 
    
def debug_print(msg, level):
    '''print the debug information'''
    dbgmsg = '[DBG L%d]| %s' %(level, msg)
    logging.debug(dbgmsg)


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
    logging.info("| " + msg)
    

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

def info_print_banner(header):
    '''print information as banner'''
    info_print("\n")
    info_print(CMD_SEP)
    info_print(header)
    info_print(CMD_SEP)


def check_passed(check_item_name):
    '''print check passed info'''
    info_print("%s Check ... PASS" % check_item_name)


