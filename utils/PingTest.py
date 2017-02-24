#--*-- coding:utf-8 --*--
'''
Created on 2015��6��15��

@author: stm
'''
import os
import platform

class PingTest(object):
    '''
    classdocs
    '''

    def __init__(self, start_ip, count):
        self.start_ip = start_ip
        self.count = count
        
        
    def pingtest(self, ip):
        ping_cmd = "ping -c 3 %s"
        if "Windows" == platform.system():
            ping_cmd = "ping -n 3 %s"
        ret = os.system(ping_cmd % ip)
        
        if 0 == ret:
            return True
        else:
            return False
        
    def getAvailableIP(self):
        ip_base, ip_surfix = self.start_ip.rsplit(".", 1)
        
        avail_ip = self.start_ip
        
        for cnt in range(1, self.count+1):
            _ip_surfix = int(ip_surfix) + cnt 
            ip_mixed = "%s.%s" % (ip_base, _ip_surfix)
            
            if self.pingtest(ip_mixed):
                avail_ip = ip_mixed
                break
                
        return avail_ip
        