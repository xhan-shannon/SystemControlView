#--*-- coding:utf-8 --*--
'''
Created on 2015��6��30��

@author: stm
'''
import re

class IPCheck(object):
    '''
    Check ip format
    '''
    @staticmethod
    def ip_format_check(ip_str):
        pattern = r"\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
        if re.match(pattern, ip_str):
            return True
        else:
            return False