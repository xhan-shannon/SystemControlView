'''


@author: stm
'''
import unittest
from engine import ServerEng
from utils import DebugLog



class Test(unittest.TestCase):


#     def testLogin(self):
#         s1 = ServerEng.ServerEng(None, None)
#         s1.modify_passwd_and_accept_license(1, "192.168.9.11")
#         
#     def testInstallSoftware(self):
#         s1 = ServerEng.ServerEng(None, None)
#         s1.install_software(1 , '["192.168.9.22"]')
#         
    def testSetDefaultIP(self):
        s1 = ServerEng.ServerEng(None, None)
        s1.set_default_ip(1 , '["192.168.9.21", "060A17A"]')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    DebugLog.init_log(True, True)
    DebugLog.loglevel1 = True
    unittest.main()