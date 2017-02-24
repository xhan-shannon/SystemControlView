# -*- coding: utf-8 -*-
'''
Created on 2015��1��13��

@author: stm
'''


from threading import Thread
import pdb
from multiprocessing.process import Process
import re
from base.OpenBrowser import BrowserConn
from utils import DebugLog
import time
#from pyvirtualdisplay import Display

class ASMi(object):
    '''
    The class maintains the HMC connection
    '''
    OPERATION_SPEED = 5

    (Power_Restart_Control, System_Service_Aids,
     System_Information, System_Configuration,
     Network_Services) = range(0, 5)

    menu_link = {Power_Restart_Control: 'i79',
                 System_Service_Aids: 'i80',
                 System_Information: 'i81',
                 System_Configuration: 'i82',
                 Network_Services: 'i83'
                 }
    
    
    menu_link_xpath = {Power_Restart_Control: '//*[@id="navigation"]/input[2]',
                 System_Service_Aids: '//*[@id="navigation"]/input[4]',
                 System_Information: '//*[@id="navigation"]/input[6]',
                 System_Configuration: '//*[@id="navigation"]/input[8]',
                 Network_Services: '//*[@id="navigation"]/input[10]'
                 }

    menu_item_link_desc = {'Power On/Off System': 'Power On/Off System',
         'Immediate Power Off': 'Immediate Power Off',
         'Factory Configuration': 'Factory Configuration',
         'Real-time Progress Indicator':'Real-time Progress Indicator',
         'Hardware Management Consoles':'Hardware Management Consoles'
         }



    def __init__(self, ip):
        '''
        Constructor
        '''
        #self.display = Display(visible=0, size=(800, 600))
        #self.display.start()
        self.window_stack = list()
        self.client = self.open(ip)
        
    
    def open(self, ip):
        self.clientbrowser = BrowserConn(True, ip)
        self.driver = self.clientbrowser.start()
        #clientbrowser.login(driver, username, password)
        #time.sleep(15)
        self.window_stack.append(self.driver.current_window_handle)
        # self.test_frame()
        
    
    def get_cur_avail_window(self):
        '''return the top window handle'''
        if    self.window_stack:     # not empty
            return self.window_stack[-1]
        else:
            return None
            
            
    def test_frame(self):
        '''test the frames'''
        DebugLog.info_print(unicode(self.driver.page_source))
        self.driver.switch_to_frame('toc_frame')
        DebugLog.info_print(unicode(self.driver.page_source))
        self.driver.switch_to_default_content()
        DebugLog.info_print(unicode(self.driver.page_source))
        
        
    def get_serial_number(self):
        '''return the serial number for the target'''
        self.driver.switch_to_frame('form_frame')
        body_text = self.driver.find_element_by_xpath('//html/body').text
        pattern = 'Serial number: (\w+)'
        serial_number_match = re.search(pattern, body_text)
        serial_number = serial_number_match.group(1)
        self.driver.switch_to_default_content()
        return serial_number
        
        
    def get_uname_input(self, driver):
        '''get the uname input element control'''
        return driver.find_element_by_xpath('//*[@name="user"]')
    
    
    def get_passwd_input(self, driver):
        '''get the password input element control'''
        return driver.find_element_by_xpath('//*[@name="password"]')
    
        
    def get_login_button(self, driver):
        '''get the login button'''
        return driver.find_element_by_xpath('//*[@id="Log in"]')


    def _expand_menu_link(self, item):
        # expand the power on/off system link
        self.driver.switch_to_frame('toc_frame')
        expand_elem = self.driver.find_element_by_xpath(ASMi.menu_link_xpath[item])
        expand_status_text = expand_elem.get_attribute("title")
        DebugLog.debug_print_level1(expand_status_text)
        # 'Expand this menu'
        expected_str = 'Expand'
        if expected_str in expand_status_text:
            DebugLog.debug_print_level1("click the link to expand the menu link")
            expand_elem.click()


    def expand_power_restart_control_link(self):
        '''expand the power on/off system link'''
        self._expand_menu_link(ASMi.Power_Restart_Control)
            
            
    def expand_system_service_aids_link(self):
        '''expand the system service aids  link'''
        self._expand_menu_link(ASMi.System_Service_Aids)
            
            
    def expand_system_information_link(self):
        self._expand_menu_link(ASMi.System_Information)
            
            
    def expand_system_configuration_link(self):
        '''expand the system configuration link'''
        self._expand_menu_link(ASMi.System_Configuration)
    
    
    def _click_menu_item_link(self, item_name):
        # click the menu item link
        self.driver.switch_to_default_content()
        self.driver.switch_to_frame('toc_frame')
        self.driver.find_element_by_link_text(item_name).click()
        self.driver.switch_to_default_content()

    
    def click_power_on_off_system_link(self):
        '''return the link for power on/off system'''
        self._click_menu_item_link(ASMi.menu_item_link_desc['Power On/Off System'])

        
        
    def click_immediate_power_off_link(self):
        '''return the link for immediate power off'''
        self._click_menu_item_link(ASMi.menu_item_link_desc['Immediate Power Off'])
        
        
    def click_hardware_management_connections_link(self):
        '''return the link for hardware management connections'''
        self._click_menu_item_link(ASMi.menu_item_link_desc['Hardware Management Consoles'])
        
        
    def click_factory_configuration_link(self):
        '''return the link for factory configuration'''
        self._click_menu_item_link(ASMi.menu_item_link_desc['Factory Configuration'])
        
        
    def _retrieve_power_status(self):
        '''retrieve the IVM host power status'''  
        
        '''
        Status: On, Off, ...
        '''
        self.driver.switch_to_frame('form_frame')
        body_text = self.driver.find_element_by_xpath('/html/body').text
        pattern = 'Current system power state: (\w+)'
        power_status_match = re.search(pattern, body_text)
        power_status = power_status_match.group(1)
        self.driver.switch_to_default_content()
        return power_status
        
        
    def click_save_settings_and_power_off_button(self):
        '''save settings and power off'''
        self.driver.switch_to_frame('form_frame')
        self.driver.find_element_by_xpath('//*[@id="Save settings and power off"]').click()
        time.sleep(1)
        self.driver.switch_to_default_content()
        
        
    def click_save_settings_and_power_on_button(self):
        '''save settings and power on'''
        self.driver.switch_to_frame('form_frame')
        cnt1 = self.driver.find_element_by_xpath('//*[@id="ip"]')
        time.sleep(1)
        items = cnt1.find_elements_by_xpath('//option')
        for item in items:
            if item.text.startswith("Running"):
                item.click()
                break
        time.sleep(1)
        cnt2 = self.driver.find_element_by_xpath('//*[@id="prt"]')
        time.sleep(1)
        items = cnt2.find_elements_by_xpath('//option')
        for item in items:
            if item.text.startswith("AIX"):
                item.click()
                break
        time.sleep(1)
        self.driver.find_element_by_xpath('//*[@id="Save settings and power on"]').click()
        time.sleep(1)
        self.driver.switch_to_default_content()
        
        
        
    def click_save_settings_button(self):
        '''save settings and power on'''
        self.driver.switch_to_frame('form_frame')
        cnt1 = self.driver.find_element_by_xpath('//*[@id="ip"]')
        time.sleep(1)
        items = cnt1.find_elements_by_xpath('//option')
        for item in items:
            if item.text.startswith("Running"):
                item.click()
                break
        time.sleep(1)
        cnt2 = self.driver.find_element_by_xpath('//*[@id="prt"]')
        time.sleep(1)
        items = cnt2.find_elements_by_xpath('//option')
        for item in items:
            if item.text.startswith("AIX"):
                item.click()
                break
        time.sleep(1)
        self.driver.find_element_by_xpath('//*[@id="Save settings"]').click()
        time.sleep(1)
        self.driver.switch_to_default_content()
        
        
    def click_continue_button(self):
        '''get the continue button from right form,
           then click it
        '''
        self._click_elem_from_rigt_form('//*[@id="Continue"]')

                        
    def get_realtime_progress_indicator_link_status(self):
        '''return the link for real-time progress indicator'''
        DebugLog.info_print("pop up progress id\ndicator window")
        self.driver.switch_to_frame('toc_frame')
        self.expand_system_information_link()
        saved_handles_set = set(self.driver.window_handles)
        self.driver.find_element_by_link_text("Real-time Progress Indicator").click()

        self.update_driver(self.driver, saved_handles_set)
#         self.window_stack.append(self.driver.current_window_handle)

        status_txt=self.driver.find_element_by_xpath('//*[@id="body-rtchkpt"]/strong/pre').text
#         self.driver.close()
#         self.driver.switch_to_window(self.get_cur_avail_window())
#         DebugLog.info_print("Got back to the last window")
#         DebugLog.info_print(self.driver.page_source)
        return status_txt
        
#         DebugLog.debug_print_level1(self.driver.page_source)
#         self.driver.close()
       
        
    def update_driver(self, driver, saved_handles_set):
        '''need update driver because there is one more new window is created'''
        cur_handles_set = set(driver.window_handles)
        sub_handles = list(set(cur_handles_set) - set(saved_handles_set))
        if len(sub_handles) == 1:
            self.driver.switch_to_window(sub_handles[0])
            
           
#      def after_confirm_system_status(self):
         
           
    def login(self, uname="admin", passwd="admin"):
        '''login the hmc'''
        locator_xpath = '//*[@id="wholeBody"]/tbody/tr/td/div/p[2]/a'
        #DebugLog.debug_print_level1(unicode(self.driver.page_source))
        self.driver.switch_to_frame("toc_frame")
        #DebugLog.debug_print_level1(unicode(self.driver.page_source))

        self.get_uname_input(self.driver).send_keys(uname)
        self.get_passwd_input(self.driver).send_keys(passwd)
        self.get_login_button(self.driver).click()            

    
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
        '''logout from asmi session'''
        DebugLog.info_print("log out asmi page")
        self.driver.switch_to_default_content()
        self.driver.switch_to_frame("status_frame")
        self.driver.find_element_by_name("submit").click()
#         self.driver.find_element_by_xpath('//*[@id="body-status"]/form/table/tbody/tr/td[1]/input').click()
        self.driver.quit()
        
        #self.display.stop()

    
    def _click_elem_from_rigt_form(self, xpath):
        # get the element from right form
        self.driver.switch_to_default_content()
        self.driver.switch_to_frame('form_frame')
        self.driver.find_element_by_xpath(xpath).click()
        time.sleep(1)
        self.driver.switch_to_default_content()


    def get_power_on_off_continue_button(self):
        '''return the continue button element, if not return None'''
        self.driver.refresh()
        time.sleep(1)
        self.driver.switch_to_frame('form_frame')
        elem = self.driver.find_element_by_xpath('//*[@id="Continue"]')
        time.sleep(2)
        self.driver.switch_to_default_content()
        
        return elem


    def get_power_status(self):
        '''return the ivm host power status from asmi page'''
        self.expand_power_restart_control_link()
        self.click_power_on_off_system_link()
        power_status = self._retrieve_power_status()
        return power_status


    def click_reset_server_firmware_settings(self):
        '''select reset server firmware settings'''
        self._click_elem_from_rigt_form('//*[@id="Reset server firmware settings"]')


    def reset_server_firmware_settings(self):
        '''Go to System Service Aids, 
           click on Factory Configuration, 
           then click on Reset server firmware settings option.
        '''
        self.expand_system_service_aids_link()
        time.sleep(1)
        self.click_factory_configuration_link()
        time.sleep(1)
        self.click_reset_server_firmware_settings()
        time.sleep(1)
        self.click_continue_button()
        time.sleep(2)
        self.click_continue_button()
        time.sleep(2)
        
        
    def poweron(self):
        self.expand_power_restart_control_link()
        time.sleep(1)
        self.click_power_on_off_system_link()
        time.sleep(1)
        self.click_save_settings_and_power_on_button()
        
        
    def savesettings(self):
        self.expand_power_restart_control_link()
        time.sleep(1)
        self.click_power_on_off_system_link()
        time.sleep(1)
        self.click_save_settings_button()
        


    def click_reset_to_non_HMC_managed_configuration(self):
        '''click the reset button'''
        self._click_elem_from_rigt_form(\
             '//*[@id="Reset the server to a non-HMC managed configuration"]')


    def click_remove_connection(self):
        '''click the remove connection button'''
        self._click_elem_from_rigt_form('/html/body/form/div/p/input')
    
    
    def reset_server_to_non_HMC(self, target_ip):
        '''reset a server to non-HMC state'''

        # Todo list
        # expand 'System Configuration'
        # select 'Hardware Management Consoles'
        # select the hmc items
        # click remove connection button
        self.expand_system_configuration_link()
        time.sleep(1)
        self.click_hardware_management_connections_link()
        time.sleep(1)
        self.click_reset_to_non_HMC_managed_configuration()
        time.sleep(1)

    
    def __del__(self):
        '''
        destructor for asmieng
        logout from asmi page
        '''
        DebugLog.info_print("asmi engine destructor")
        self.logout()
        











    
    
    
        

    
     
