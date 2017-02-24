#--*-- coding:utf-8 --*--

'''
Created on 2015��5��8��

@author: stm
'''
import unittest
from utils import DebugLog
from base.vdcommcnt import VdCommCenter



class Test(unittest.TestCase):


#     def testConstructor(self):
#         inst_vdcommcen = VdCommCenter()
#         
#         print "just test unittest for vdcommcenter "
#         #self.assertIn(member, container, msg)

    def testVdCommCenterStart(self):
        DebugLog.init_log(logfile=True)
        DebugLog.loglevel1 = True
        print "In testVdCommCenterStart"
        inst_vdcommcen = VdCommCenter()
        
        inst_vdcommcen.sendDelayedMessage("1234:_,test12345")
        inst_vdcommcen.sendDelayedMessage("abcd:_,testabcd")
        inst_vdcommcen.sendDelayedMessage("!@#$:_,test!@#$")
        
        
        inst_vdcommcen.start()
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testConstructor']
    DebugLog.init_log(logfile=True)
    unittest.main()