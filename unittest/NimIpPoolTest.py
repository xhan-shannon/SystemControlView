'''
Created on 2015

@author: stm
'''
import unittest
from utils.NimIPPool import NimIPPool


class NimIpPoolTest(unittest.TestCase):


    def testTwoInstances(self):
        a = NimIPPool()
        b = NimIPPool()
        for idx in range(1, 100):
            a_ip = a.getAvailableIP('060AAEA%d ' % idx)
            b_ip = b.getAvailableIP("0010001%d" % idx)
            print a_ip
            print b_ip
            a.releaseIP(a_ip)

        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testTwoInstances']
    unittest.main()