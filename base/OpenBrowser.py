# -*- coding: utf-8 -*-
'''
@author: stm
'''
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from utils.ErrorHandler import NoBrowserOpenedError, Login_Error
from utils import DebugLog



IMPLICITY_WAIT_TIMEOUT = 60


class BrowserConn(object):
    '''
    Connect firefox
    '''

    def __init__(self, bsecure, svrip, svrport=None):
        '''
        initialize the connection
        '''
        urlprefix = "http"
        if bsecure:
            urlprefix = "https"
            
        self.url = urlprefix + "://%s" % svrip
        
        if svrport:
            self.url += ":%s" % svrport
            

    def start(self, browser_type="firefox", implicity_wait_timeout=IMPLICITY_WAIT_TIMEOUT):
        '''
        To open a browser
        '''
        browser = None
        if browser_type.startswith('Chrome'):
            browser_chrome = webdriver.Chrome()
            browser = browser_chrome
        else:
            browser_firefox = webdriver.Firefox()
            browser = browser_firefox
        #browser = webdriver.Firefox()
        
        if not browser:
            raise(NoBrowserOpenedError("No browser opened"))
        
        browser.implicitly_wait(implicity_wait_timeout)
        browser.get(self.url)

        return browser
    
    
    def start_htmlunit(self, implicity_wait_timeout=60):
        browser = webdriver.Remote(desired_capabilities=DesiredCapabilities.HTMLUNIT)
        browser.implicitly_wait(implicity_wait_timeout)
        browser.get(self.url)
        
    
    def login(self, driver, username, password):
        '''
        Use default configurations in shared_config file to login PD
        '''
            
        pd_browser_client = driver
    
        DebugLog.info_print("Login PowerDirector")
        assert "PowerDirector" in pd_browser_client.title
        DebugLog.info_print("Page title: " + pd_browser_client.title)
    
        pd_browser_client.implicitly_wait(30)
        uid_input = pd_browser_client.find_element_by_id("uid")
        uid_input.send_keys(username)
        p_input = pd_browser_client.find_element_by_id("pword")
        p_input.send_keys(password)
        login_button = pd_browser_client.find_element_by_xpath("/html/body/div/form/div/p[4]/input")
        login_button.click()
        expect_welcome_panel = pd_browser_client.find_element_by_id("user_panel")
        welcome_text = "PowerDirector"
    
        try:
            if welcome_text in expect_welcome_panel.text:
                print( expect_welcome_panel.text)
        except:
            raise Login_Error("Login fails")
            pd_browser_client.quit()
    
        return pd_browser_client
