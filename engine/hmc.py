# -*- coding: utf-8 -*-
'''
Created on 2015��1��13��

@author: stm
'''
from OpenBrowser import BrowserConn
import time
import DebugLog
import OpenBrowser
from selenium.common.exceptions import NoSuchElementException
from threading import Thread
import pdb
from multiprocessing.process import Process

class HMC(object):
    '''
    The class maintains the HMC connection
    '''
    
    def __init__(self, ip):
        '''
        Constructor
        '''
        self.window_stack = list()
        self.client = self.open(ip)
        
       
    
    def open(self, ip):
        self.clientbrowser = BrowserConn(True, ip)
        self.driver = self.clientbrowser.start()
        #clientbrowser.login(driver, username, password)
        #time.sleep(15)
        self.window_stack.append(self.driver)


    def get_uname_input(self, driver):
        '''get the uname input element control'''
        return driver.find_element_by_xpath('//*[@id="div1"]/form/table/tbody/tr[1]/td[2]/input')
    
    
    def get_passwd_input(self, driver):
        '''get the password input element control'''
        return driver.find_element_by_xpath('//*[@id="div1"]/form/table/tbody/tr[2]/td[2]/input')
    
    
    
    def get_login_button(self, driver):
        '''get the login button'''
        return driver.find_element_by_xpath('.//*[@id="div1"]/form/p/input[1]')
    
    
    def detect_unterminated_session(self, driver):
        '''check if there is unterminated session exists'''
        try:
            driver.set_script_timeout(10)
            driver.find_element_by_xpath('/html/body/span/form/span/input[2]')
        except NoSuchElementException:
            return False
        finally:
            driver.set_script_timeout(OpenBrowser.IMPLICITY_WAIT_TIMEOUT)
    
        return True
        
    
    def create_new_session(self, driver):
        '''click the new session button'''
        xpath = '/html/body/span/form/span/input[2]'
        new_session_btn = driver.find_element_by_xpath(xpath)
        new_session_btn.click()
     

    
    def update_driver(self, driver, saved_handles_set):
        '''need update driver because there is one more new window is created'''
        cur_handles_set = set(driver.window_handles)
        sub_handles = list(set(cur_handles_set) - set(saved_handles_set))
        if len(sub_handles) == 1:
            self.driver.switch_to_window(sub_handles[0])
            DebugLog.debug_print_level1(unicode(self.driver.page_source))
    
    
    def login(self, uname, passwd):
        '''login the hmc'''
        locator_xpath = '//*[@id="wholeBody"]/tbody/tr/td/div/p[2]/a'
        #DebugLog.debug_print_level1(unicode(self.driver.page_source))
        self.driver.switch_to_frame(0)
        #DebugLog.debug_print_level1(unicode(self.driver.page_source))
        locator_elem = self.driver.find_element_by_xpath(locator_xpath)
        locator_elem.click()
        self.get_uname_input(self.driver).send_keys(uname)
        self.get_passwd_input(self.driver).send_keys(passwd)
        self.get_login_button(self.driver).click()
        
        saved_handles_set = set(self.driver.window_handles)
        # if there is session which is not terminated, then create a new one.
        if self.detect_unterminated_session(self.driver):
            self.create_new_session(self.driver)
            self.update_driver(self.driver, saved_handles_set)
            
        self.window_stack.append(self.driver)
            
    
    def get_logout_link(self, driver):
        '''get the logout link element'''
        #driver.switch_to_frame(0)
        DebugLog.info_print("Before switch to frame hmcmainui")
        driver.switch_to_frame('hmcmainui')
        DebugLog.debug_print_level1(unicode(self.driver.page_source))
        DebugLog.info_print("After switch to frame hmcmainui")
        #driver.switch_to_frame(0)
        DebugLog.info_print("Before switch to frame toolbar_frame")
        driver.switch_to_frame('toolbar_frame')
        DebugLog.debug_print_level1(unicode(self.driver.page_source))
        DebugLog.info_print("After switch to frame toolbar_frame")
        link_elemt = driver.find_element_by_xpath('//*[@id="logoffLink"]')
        return link_elemt
    
    
    def get_logoff_confirm_button(self, driver):
        '''get the confirm ok button in the logoff dialog'''
        elemt = driver.find_element_by_xpath('/html/body/span/table/tbody/tr/td/form/span/input')
        return elemt
    
    def post_click_action(self, elemt):
        elemt.click()
            
            
    
    
    def logout(self):
        '''logout from hmc session'''
        
        #self.driver.switch_to_default_content()
        
        # save the current window handles
        DebugLog.debug_print_level1(unicode(self.driver.page_source))
        saved_handles_set = set(self.driver.window_handles)
        logout_elemt_link = self.get_logout_link(self.driver)
        #import pdb; pdb.set_trace()
        
#         print "Before creating process to click the logoff link"
#         forkproc = Process(target=self.post_click_action, args=(logout_elemt_link,))
#         print "After creating process, " + str(forkproc.is_alive())
#         forkproc.start()
#         print "After creating process, and start it. " + str(forkproc.is_alive())
        print "Before creating process to click the logoff link"
        forkedthread = Thread(target=self.post_click_action, args=(logout_elemt_link,))
        print "After creating process, " + str(forkedthread.is_alive())
        forkedthread.start()
        print "After creating process, and start it. " + str(forkedthread.is_alive())
        
        DebugLog.info_print("After click the logout link")
        
        pdb.set_trace()
        while forkedthread.is_alive():
            DebugLog.info_print("The forked process is running")
            #self.update_driver(self.driver, saved_handles_set)
            
            #pdb.set_trace()
            
            time.sleep(10)
            self.driver.close()
        
        
        self.update_driver(self.driver, saved_handles_set)
        DebugLog.debug_print_level1(unicode(self.driver.page_source))
        ok_btn_elemt = self.get_logoff_confirm_button(self.driver)
        ok_btn_elemt.click()

        
        
        
    def remove_conn(self, target_ip):
        pass
    
    
     