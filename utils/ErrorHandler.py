# -*- coding: utf-8 -*-
'''
Created on 2014年12月18日

@author: stm
'''


EXPECTED_OS_NAME = 'AIX'
EXPECTED_OS_VERSION = '2.2.3.1'

class ActionIsNotExpected_Exception(Exception):
    '''ActionIsNotExpected_Exception'''
    def __str__(self):
        return "The action is not expected for the current state."
               
    def __unicode__(self):
        return "执行的动作不是当前状态期望的动作"

class WrongOSTargetVersion_Exception(Exception):
    '''Wrong OS target'''
    def __str__(self):
        return "The target OS version is not greater than %s." % EXPECTED_OS_VERSION
               
    def __unicode__(self):
        return "目标系统版本大于%s" % EXPECTED_OS_VERSION
    
class MissingSoftware_Exception(Exception):
    '''The specific exception for software package checking'''
    def __init__(self, msg):
        
        self.msg = msg
        
    def __str__(self):
        return "Please check if the software package %s is installed." \
               % self.msg
               
    def __unicode__(self):
        return "请检查软件包 %s 是否已经安装" % self.msg
    
    
class TemplateNotMounted_Exception(Exception):
    '''The specific exception:template is mounted for software package checking'''
        
    def __str__(self):
        return "Please check if the template director is mounted"
               
    def __unicode__(self):
        return "请检查template目录 是否已经挂载"


class PowerDirectorNotInstalled_Exception(Exception):
    pass


class ConfigFileError(Exception):
    '''Read config file error'''
    def __init__(self, msg):
        
        self.msg = msg
        
    def __str__(self):
        return self.msg
               
    def __unicode__(self):
        return "请检查配置文件 %s 是否已经存在" % self.msg
    

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
        return "SSH连接失败"
    
    
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
        return "没有提供源软件包或者源安装包路径不正确"
    
    
class PackagePath_Error(Exception):
    '''Read config file error'''
    def __str__(self):
        return "Package path is not provided"
               
    def __unicode__(self):
        return "没有提供软件包路径"
    
    
class PackageVersionNumber_Error(Exception):
    '''Read config file error'''
    def __str__(self):
        return "Package version number is not provided"
               
    def __unicode__(self):
        return "没有提供软件版本号"
    
class DiskSizeNotEnough_Error(Exception):
    '''Read config file error'''
    def __str__(self):
        return "Disk size is not enough"
               
    def __unicode__(self):
        return "磁盘空间不足"
    
class NoBrowserOpenedError(object):
    '''Open browser failed'''
    def __str__(self):
        return "Open browser failed"
               
    def __unicode__(self):
        return "打开浏览器错误"

class Arguments_Exception(Exception):
    '''Wrong Arguments'''

    def __str__(self):
        return "The arguments are not right."

    def __unicode__(self):
        return u"参数不正确"
    
    
class Login_Error(object):
    '''User login failed'''
    def __str__(self):
        return "User login failed"
               
    def __unicode__(self):
        return "用户登录错误"
