#--*-- coding:utf-8 --*--
'''
Created on 2015��5��14��

@author: stm
'''


SERVER_STATUS = [("IPSCAN", "Server SCAN"),
            ("ADDTOHMC", "Add To HMC"),
            ("UPDATEPASSWD", "Update Password"),
            ("RECOVERPROFILE", "Recover profile"),
            ("INSTALLVIOS", "Install VIOS"),
            ("REMVVIOS", "Remove Server From HMC"),
            ("HMCTOIVM", "Convert HMC to IVM"),
            ("REGISTERPD", "Register PD"),
            ("SHOWRECORDS", "Show Records")
            ]

class ServerStatusFSM(object):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        