'''
Created on 2015-06-30

@author: stm
'''
import unittest
from utils.IPCheck import IPCheck


class Test(unittest.TestCase):


    def testNormalIP(self):
        normal_ip_list = ["1.1.1.1", "255.255.255.255", "192.168.1.1",
                          "10.10.1.1", "132.254.111.10", "26.10.2.10",
                          "127.0.0.1",
                          ]
        for itm in normal_ip_list:
            self.assertTrue(IPCheck.ip_format_check(itm))


    def testWrongIP(self):
        normal_ip_list = ["10.10.10", "10.10", "10",
                          "a.a.a.a", "10.10.10.a", "10.10.10.256",
                          "222.222.2.999", "999.10.10.20", "2222.22.22.22",
                          "22.2222.22.2"
                          ]
        for itm in normal_ip_list:
            self.assertFalse(IPCheck.ip_format_check(itm))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testNormalIP']
    unittest.main()