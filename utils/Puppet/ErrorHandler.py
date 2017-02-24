# -*- coding: utf-8 -*-
'''
Created on 2014年12月18日

@author: stm
'''


EXPECTED_OS_NAME = 'AIX'
EXPECTED_OS_VERSION = '2.2.3.1'

class WrongOSTarget_Exception(Exception):
    '''Wrong OS target'''
    def __init__(self, target_os):
        if not target_os:
            self.target_os = EXPECTED_OS_NAME
        else:
            self.target_os = target_os
            
    def __str__(self):
        return "The target OS is not %s." % self.target_os
               
    def __unicode__(self):
        return u"目标系统不是 %s" % self.target_os

class WrongOSTargetVersion_Exception(Exception):
    '''Wrong OS target'''
    def __str__(self):
        return "The target OS version is not greater than %s." % EXPECTED_OS_VERSION
               
    def __unicode__(self):
        return u"目标系统版本大于%s" % EXPECTED_OS_VERSION
    
class MissingSoftware_Exception(Exception):
    '''The specific exception for software package checking'''
    def __init__(self, msg):
        
        self.msg = msg
        
    def __str__(self):
        return "Please check if the software package %s is installed." \
               % self.msg
               
    def __unicode__(self):
        return u"请检查软件包 %s 是否已经安装" % self.msg
    
    
class TemplateNotMounted_Exception(Exception):
    '''The specific exception:template is mounted for software package checking'''
        
    def __str__(self):
        return "Please check if the template director is mounted"
               
    def __unicode__(self):
        return u"请检查template目录 是否已经挂载"


class PowerDirectorNotInstalled_Exception(Exception):
    pass


class ConfigFileError(Exception):
    '''Read config file error'''
    def __init__(self, msg):
        
        self.msg = msg
        
    def __str__(self):
        return self.msg
               
    def __unicode__(self):
        return u"请检查配置文件 %s 是否已经存在" % self.msg
    

class ConnectFail_Error(Exception):
    '''SSH connection failed.'''
    def __init__(self, msg=None):
        self.msg = msg
        
    def __str__(self):
        tmp = 'SSH connection failed.'
        if self.msg:
            tmp = tmp + ": %s" % self.msg
        return tmp
               
    def __unicode__(self):
        return u"SSH连接失败"
    
    
class PackagePath_NotExists_Error(Exception):
    '''Read config file error'''
    def __init__(self, msg):
        
        self.msg = msg
        
    def __str__(self):
        tmp = 'Installation Package path does not exist.'
        if self.msg:
            tmp = tmp + ": %s" % self.msg
        return tmp
               
    def __unicode__(self):
        return u"没有提供源软件包或者源安装包路径不正确"
    
    
class PackagePath_Error(Exception):
    '''Read config file error'''
    def __str__(self):
        return "Package path is not provided"
               
    def __unicode__(self):
        return u"没有提供软件包路径"
    
    
class PackageVersionNumber_Error(Exception):
    '''Read config file error'''
    def __str__(self):
        return "Package version number is not provided"
               
    def __unicode__(self):
        return u"没有提供软件版本号"
    
class DiskSizeNotEnough_Error(Exception):
    '''Read config file error'''
    def __str__(self):
        return "Disk size is not enough"
               
    def __unicode__(self):
        return u"磁盘空间不足" 
    
class WrongVersionNumber_Error(Exception):
    '''Wrong versino number error handler'''
    def __init__(self, msg):
        self.msg = msg
    
    def __str__(self):
        msg = "Wrong version number"
        if self.msg:
            msg += ", the version should begin with " + self.msg 
        return msg
       
    def __unicode__(self):
        msg = u"版本号错误"
        if self.msg:
            msg += u", 版本号开头格式：'%s.x.x'" % self.msg 
        return msg