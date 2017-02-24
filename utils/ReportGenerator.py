#!/usr/bin/python
""" The report generator handles commands from the user to configure reports,
    then obtains the data from the requested file,
    then writes the report file. 
"""
import rxt
import os
import sys
import locale
import traceback
import simpl
import simplejson
import time
import datetime
import csv
import shutil
import copy
import ConfigParser
import logging
import BaseJSONListener
import SrDB
import bz2
import tarfile
import re
import sets
import types
import codecs
import reportlab
import BusyBoa
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.graphics import renderPDF
from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
# Tables
from reportlab.tools.docco.rl_doc_utils import *
# Platypus
from reportlab.platypus import Frame, PageTemplate, SimpleDocTemplate, Paragraph, Spacer, PageBreak, tableofcontents, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader

#import pdb

page_size = 15 # Should be equal with module constant!!!
normal_event_page = 500 # This is for the basic event constant
 
class reportGenerator(BaseJSONListener.BaseJSONListener):
    """reportGenerator class 
       Make reports from result *.json files in report_temp folder.
    """
    MyJSONUserError = BaseJSONListener.JSONUserError
    
    date_format = '%Y-%m-%d %H:%M:%S'
    report_info = { 'custname' : '', 
                    'contactname' : '', 
                    'custaddress' : '', 
                    'custemail' : '', 
                    'custphone' : '', 
                    'username' : '', 
                    'title' : '', 
                    'useraddress' : '',
                    'useremail' : '', 
                    'userphone' : '', 
                    'ticketid' : '', 
                    'note' : '', 
                    'comment1' : '',  
                    'comment2' : '',  
                    'comment3' : '' 
    }
    
    debug = False
    #debug = True

    def __init__(self,_debug = False):
        self.debug = _debug
        BaseJSONListener.BaseJSONListener.__init__(self, 'Report Generator')
        
        cfg_file = ConfigParser.ConfigParser()
        cfg_file.read('/etc/rxt.conf')
        id = 'System Files'
        self.temp_report_path = cfg_file.get(id, 'basedir') + 'report_temp'
        self.report_path = cfg_file.get(id, 'report')
        self.data_entry_file = cfg_file.get(id, 'data_entry')
        self.write_log('temp=%s, report=%s' % (self.temp_report_path, self.report_path))

        # Create /home/Sunrise/report_temp if it doesn not exists 
        if not os.path.isdir(self.temp_report_path):
            try:
                os.mkdir(self.temp_report_path)
            except:
                self.write_log('Test Cannot Create %s' % self.temp_report_path, 'Error', sys.exc_info())

        # Create /home/sunrise/measurement/report if it doesn not exists
        if not os.path.isdir(self.report_path):
            try:
                os.mkdir(self.report_path)
            except:
                self.write_log('Test Cannot Create %s' % self.report_path, 'Error', sys.exc_info())
        
        # saved data entry
        data = None 
        try:
            f_info = open(self.data_entry_file, 'r')
            data = f_info.read()
            f_info.close()
        except:
            self.write_log('Failed to load file "%s"!' % self.data_entry_file, 'Error', sys.exc_info())

        if data is not None:
            try:
                reportGenerator.report_info = eval(data)
            except:
                self.write_log('Failed to eval saved report info!', 'Error', sys.exc_info())
        
        # number formating         
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        self.write_log(locale.getlocale(), 'Locale:')
        self.write_log(locale.format('%.2f', 10250456.10, True), 'Number format:')
        
        # data font        
        #pdfmetrics._py_getFont(dataFontType) # not support on hw        
        pdfmetrics.getEncoding(reportEncoding)
        pdfmetrics.getTypeFace(dataFontType)
        self.dataFont = pdfmetrics.Font(dataFontType, dataFontType, reportEncoding)

    def write_log(self, message, type = 'Info', ex = None):
        if self.debug:
            print '[REPGEN]\t%s\t%s' % (type, message)
            if ex is not None:
                print '[REPGEN]\tError Type:\t%s' % ex[0]
                print '[REPGEN]\tError Value:\t%s ' % ex[1]
                print '[REPGEN]\tTraceback:\t%s\n' % traceback.extract_tb(ex[2])
        if type == 'Error' or ex is not None:
            self.log.error(message)
        else:
            self.log.debug(message)

    def send_INTERNAL_CMD(self, cmd):
        while (self.next_server_id == None):
            try:
                self.next_server_id = simpl.name_locate(self.next_server_name)
            except simpl.error, reason:
                self.write_log('Name locate error (%s) looking for %s' 
                               % (reason, self.next_server_name), 'Error', sys.exc_info())
            except:
                self.write_log('Other Exception.', 'Error', sys.exc_info())
            time.sleep(0.5)

        if self.next_server_id is not None:
            return simplejson.loads(simpl.Send(self.next_server_id, simplejson.dumps(cmd), 1))
        else:
            self.write_log('Error in send_INTERNAL_CMD\n', 'Error')
            return None

    def do_SET_DATE_FORMAT(self, params):        
        self.date_format = params['format']
        self.write_log("Setting Date Format: %s" % self.date_format)

    def do_SET_REPORT_INFO (self, params):
        """Receive messages from other processes to configure and create reports
           @type  params: dictionary
           @param params: command received by the "reportGenerator"
           @return: dictionary           
        """
        
        params.pop('')
        reportGenerator.report_info.update(params)
    
        try:
            f_info = open(self.data_entry_file, 'w')
            f_info.write(str(reportGenerator.report_info))
            f_info.close()
        except:
            self.write_log('Failed to write file "%s"!' % self.data_entry_file, 'Error', sys.exc_info())

        resp = {}
        resp['_'] = 'SET-REPORT-INFO'
        resp['rc'] = 0
        resp['cmdresp'] = 0
        return resp

    def do_RTRV_REPORT_INFO (self, params):
        """Receive messages from other processes to configure and create reports
           @type  params: dictionary
           @param params: command received by the "reportGenerator"
           @return: dictionary           
        """
        
        resp = {}
        resp = reportGenerator.report_info
        resp['_'] = 'RTRV-REPORT-INFO'
        
        return resp

    def read_data_from_files(self, params):

        file_lookup = {0: 'config',
                       1: 'vcat',
                       2: 'result_otn',
                       3: 'result_sonet',
                       4: 'result_sdh',
                       5: 'result_wan',
                       7: 'result_rfc2544',
                       8: 'result_iptest',
                       9: 'result_loopback',
                      10: 'result_monitor',
                      11: 'result_e4',
                      12: 'result_e3',
                      13: 'result_e2',
                      14: 'result_e1',
                      15: 'result_ds3',
                      16: 'result_ds2',
                      17: 'result_ds1',
                      18: 'result_error',
                      19: 'result_y156sam',
                      20: 'result_fc_bert',
                      21: 'result_fc_rfc2544',
                      22: 'result_fc_loopback',
                      23: 'result_fc_b2b',
                      24: 'result_capture',
                      25: 'moduleinfo'
                      }
        '''
                      26: 'event_#',
                      27: 'rfc2544_event_#',
                      28: 'result_#',
                      29: 'y156sam_event_#'
                      30: 'fc_rfc2544_event_#'
                      31: 'fc_b2b_event'
        '''

        self.write_log(os.listdir(self.temp_report_path), 'Result files:\n')

        results = {}
        for f in file_lookup:
            fstr = file_lookup[f]
            file_name = '%s.json' % fstr
            read_file = os.path.join(self.temp_report_path, file_name)
            try:
                results[fstr] = None
                fd = open(read_file, 'r')
                try:
                    data = fd.read()
                    fd.close()
                    data = data.replace(':true', ':True')
                    data = data.replace(':false', ':False')
                    results[fstr] = eval(data.strip('\n'))
                except:
                    self.write_log('Evaluation data error for file "%s"!' % file_name, 'Error', sys.exc_info())
                    results[fstr] = None
                self.write_log('Result file "%s" loaded!' % file_name)
            except:
                #self.write_log('Result file "%s" missing!' % file_name)
                results[fstr] = None

        results['result'] = {}
        for sno in range(18):
            file_name = 'result_%d.json' % sno
            result_file = os.path.join(self.temp_report_path, file_name)
            try:
                results['result'][sno] = {}
                fd = open(result_file, 'r')
                try:
                    results['result'][sno] = eval(fd.readline().strip('\n'))
                except:
                    self.write_log('Evaluation data error for file "%s"!' % file_name, 'Error', sys.exc_info())
                fd.close()
                self.write_log('Result file "%s" loaded!' % file_name)
            except:
                #self.write_log('Stream result file "%s" missing!' % file_name)
                results['result'][sno] = None

        pageNo = 0
        results['event'] = {}
        cnt_sum = 0 
        while True:
            file_name = 'event_%d.json' % pageNo
            event_file = os.path.join(self.temp_report_path, file_name)
            if not os.path.exists(event_file): 
                break
            try:
                results['event'][pageNo] = {}
                fd = open(event_file, 'r')
                results['event'][pageNo] = eval(fd.readline().strip('\n'))
                fd.close()
                self.write_log('Event file "%s" loaded!' % file_name)
                page_event = results['event'][pageNo]['event']
                #cnt_sum = page_event['sno'] * normal_event_page + page_event['count']
                cnt_sum += page_event['count']
                pageNo += 1
                if cnt_sum == page_event['total']:                    
                    break;
            except:
                self.write_log('Event File processing fail!', 'Error', sys.exc_info())
                break;
        results['event']['totalpages'] = pageNo
        
        pageNo = 0
        results['rfc2544_event'] = {}
        while True:
            file_name = 'rfc2544_event_%d.json' % pageNo
            event_file = os.path.join(self.temp_report_path, file_name)
            if not os.path.exists(event_file): 
                break
            try:
                fd = open(event_file, 'r')
                results['rfc2544_event'][pageNo] = eval(fd.read().strip('\n'))
                fd.close()
                pageNo += 1
                self.write_log('RFC2544 result event file "%s" loaded!' % file_name)
            except:
                self.write_log('RFC2544 reselt event file processing fail!', 'Error', sys.exc_info())
                break;

        pageNo = 0
        results['y156sam_event'] = {}
        while True:
            file_name = 'y156sam_event_%d.json' % pageNo
            event_file = os.path.join(self.temp_report_path, file_name)
            if not os.path.exists(event_file): 
                break
            try:
                fd = open(event_file, 'r')
                results['y156sam_event'][pageNo] = eval(fd.read().strip('\n'))
                fd.close()
                pageNo += 1
                self.write_log('y156sam result event file "%s" loaded!' % file_name)
            except:
                self.write_log('y156sam reselt event file processing fail!', 'Error', sys.exc_info())
                break;

        pageNo = 0
        results['fc_rfc2544_event'] = {}
        while True:
            file_name = 'fc_rfc2544_event_%d.json' % pageNo
            event_file = os.path.join(self.temp_report_path, file_name)
            try:
                fd = open(event_file, 'r')
                results['fc_rfc2544_event'][pageNo] = eval(fd.read().strip('\n'))
                fd.close()
                pageNo += 1

            except:
                break;
        results['fc_rfc2544_event_page'] = pageNo;

        results['fc_b2b_event'] = {}
        file_name = 'fc_b2b_event.json'
        event_file = os.path.join(self.temp_report_path, file_name)
        try:
            fd = open(event_file, 'r')
            results['fc_b2b_event'] = eval(fd.read().strip('\n'))
            fd.close()
        except:
            #self.write_log('read fc_b2b_event data Fail', 'Error')
            pass

        return results

    def getTestmodeLabel(self, mode):
        testmode = {'SINGLE':"Single Point to Point", 'LINETHRU':"Single Line Through", 'PAYLOADTHRU':"Payload Through", 
                    'MONITOR':"Monitor", 'RFC2544':"RFC2544", 'THROUGHPUT':"Throughput", 
                    'LOOPBACK':"Loopback", 'IP':"IP", 'Y156SAM':"IntelliSAM",
                    'FC_BERT':"FC Throughput", 'FC_LOOPBACK':"FC Loopback", 'FC_RFC2544':"FC RFC2544", 
                    'FC_B2B':"FC B2B"}
        return testmode[mode]
        
    def do_CRTE_RESULTS_REPORT (self, params):
        """Receive messages from other processes to configure and create reports
           @type  params: dictionary
           @param params: command received by the "reportGenerator"
           @return: dictionary           
        """
        
        self.write_log(params, 'Command Json:\n')

        self.report_status = 'COMPLETE'
        self.test_mode = params['testmode']
        self.report_file_name = ""        
        report_file_path = ""        
        self.failReason = ""
        testmode = ('SINGLE', 'LINETHRU', 'PAYLOADTHRU', 
                    'MONITOR', 'RFC2544', 'THROUGHPUT', 'LOOPBACK', 'IP', 'Y156SAM',
                    'FC_BERT', 'FC_LOOPBACK', 'FC_RFC2544', 'FC_B2B')
        if self.test_mode not in testmode:
            self.write_log('Invalid test mode "%s"!!!' % self.test_mode, 'Error')
        
        self.write_log('START crte_results_report')
        
        pdf_file_exist = False
        pdf_file_name = ""
        pdf_file_path = ""
        if params['PDFfile']:
            pdf_file_name = params['filename'].split('.')[0] + '.pdf'
            pdf_file_path = os.path.join(self.report_path, pdf_file_name)
            if os.path.exists(pdf_file_path):
                pdf_file_exist = True;
                
        csv_file_exist = False
        csv_file_name = ""
        csv_file_path = ""
        if params['CSVfile']:
            csv_file_name = params['filename'].split('.')[0] + '.csv'
            csv_file_path = os.path.join(self.report_path, csv_file_name)
            if os.path.exists(csv_file_path):
                csv_file_exist = True
                
        if pdf_file_exist or csv_file_exist:
            if pdf_file_exist and csv_file_exist:
                message = 'Report Name, "%s" and "%s", Already Exist!' % (pdf_file_name, csv_file_name)
            elif pdf_file_exist:
                message = 'Report Name, "%s", Already Exists!' % (pdf_file_name)
            else:
                message = 'Report Name, "%s", Already Exists!' % (csv_file_name)
                   
            # remove tmp data
            try:
                os.system('rm %s/*.json' % self.temp_report_path)
            except:
                message = 'Cant remove tmp json file from path "%s"' % self.temp_report_path
                self.write_log(message, 'Error', sys.exc_info())
            
            self.write_log(message, 'Warning')
            return {'status': 'FAIL', 'reason': message}

        meas_data = self.read_data_from_files(params) # all loaded test data
        # remove tmp data
        try:
            os.system('rm %s/*.json' % self.temp_report_path)
        except:
            message = 'Cant remove tmp json file from path "%s"' % self.temp_report_path
            self.write_log(message, 'Error', sys.exc_info())
        config = meas_data['config'] # configuration data if exists
        
        self.write_log('Report generation for test_mode ==> %s' % self.test_mode)

        try:
            if params['CSVfile'] or params['PDFfile']:               

                now = time.localtime()
                self.reportDateTime = time.strftime(self.date_format, now)
                
                self.primaryPortID = NA
                self.secondaryPortID = NA
                
                self.module_info = {}
                try:
                    if 'moduleVersion' in params:
                        self.module_info['version'] = params['moduleVersion']
                    if 'moduleSerialNumber' in params: 
                        self.module_info['SN'] = params['moduleSerialNumber']
                    #print 'meas_data.moduleinfo = ',meas_data['moduleinfo']
                    if meas_data.has_key('moduleinfo') and meas_data['moduleinfo']['rc'] == 0:
                        moduleinfo = meas_data['moduleinfo']['moduleinfo']
                        self.module_info['version'] = moduleinfo['moduleVersion']
                        self.module_info['SN'] = moduleinfo['serialNumber']
                    
                    self.write_log('---------Module Info-------------')
                    self.write_log('Version: %s' % get_param(self.module_info, 'version'))
                    self.write_log('Serial Number: %s' % get_param(self.module_info, 'SN'))
                    self.write_log('---------------------------------')
                except:
                    self.write_log('System info not found!', 'Error', sys.exc_info())

                self.testStart = NA
                self.testStop = NA
                try:
                    testEvents = meas_data['event'][0]['event']
                    count = testEvents['count'];
                    while count > 0:
                        count = count - 1
                        event = testEvents['%s' % count]
                        event_type = event['type']                           
                        if event_type == 'START_MEAS':
                            self.testStart = event['time']
                            break;
                except:
                    self.write_log('Start / Stop Meas events not found!', 'Error', sys.exc_info())
                        
                try:
                    last_page = meas_data['event']['totalpages'] - 1
                    testEvents = meas_data['event'][last_page]['event']
                    count = testEvents['count'];
                    while count > 0:
                        count = count - 1
                        event = testEvents['%s' % count]
                        event_type = event['type']                           
                        if event_type == 'STOP_MEAS':
                            self.testStop = event['time']
                            break;
                except:
                    self.write_log('Stop Meas events not found!', 'Error', sys.exc_info())

                if (self.test_mode == "SINGLE" or \
                    self.test_mode == 'LINETHRU' or \
                    self.test_mode == 'PAYLOADTHRU'):
                    self.isTransport = True
                else:
                    self.isTransport = False
                    

                if params['CSVfile']:
                    self.report_file_name = csv_file_name
                    report_file_path = csv_file_path

                    try:   
                        f = open(report_file_path, "wb")
                    except:
                        message = 'Fails to open: "%s"' % report_file_path
                        self.write_log(message, 'Critical Error', sys.exc_info())                        
                        return {'status': 'FAIL', 'reason': message}

                    w = csv.writer(f)
                    
                    # Write title
                    title = ['#RxT-TEN Measurement Report for %s' % self.getTestmodeLabel(self.test_mode)]
                    w.writerow(title)

                    # Add report date and time info
                    filename = ['#Report Name: %s' % self.report_file_name]
                    w.writerow(filename)                    

                    reportCreated = ['#Report was created: %s' % (self.reportDateTime)]
                    w.writerow(reportCreated)

                    # System Information
                    self.systemInfoTable(w, meas_data, 'csv')
                    
                    # User Information
                    self.customerData(w, 'csv')
                    
                    # Comments
                    self.comments(w, 'csv')
                    
                    # Measurement setup data
                    if self.test_mode.startswith("FC_"):
                        self.measSetupFC(w, config, 'csv')
                    else:
                        self.measSetup(w, config, 'csv')

                    if (self.isTransport):         
                        self.sdhMeasParam(w, config, 'csv')  
                        # Write sdh port setup
                        self.sdhPortSetup(w, config, 'csv')
                        self.sdhInterfaceSetup(w, config, 'csv')
                        self.sdhRxTxSettingSetup(w, config, 'csv')
                        # Write Summary data
                        if params['summary']:
                            self.summaryTableSdh(w,meas_data, 'csv')

                        # Write test event log data
                        if params['eventlog']:
                            self.eventTable(w,meas_data, 'csv')
                        
                        #Write SDH result data
                        #get_param_format
                        results = meas_data['result_sdh']['result']
                        #NW_SDH = 0 
                        #NW_SONET = 1
                        
                        nw_standard = self.getNwStandard(meas_data) 
                        isLP = self.isLP(meas_data)
                        isTU3 = self.isTU3(meas_data)
                        if params['Signal']:
                            self.signalTable(w, results, 'csv')
                        if params['sdh']:
                            self.sdhTable(w, results, nw_standard, isLP, isTU3, 'csv')
                        ptn="None"
                        if config['config']['rx_standard'] == 'SDH':
                            bert_type = config['config']['stm']['bert']['rx_pattern']['mode']
                            ptn       = config['config']['stm']['bert']['rx_pattern']['type']
                        elif config['config']['rx_standard'] == 'SONET':
                            bert_type = config['config']['sonet']['bert']['rx_pattern']['mode']
                            ptn       = config['config']['sonet']['bert']['rx_pattern']['type']
                        else:
                            bert_type = config['config']['otn']['bert']['rx_pattern']['mode']
                        
                        isEnM2101 = False
                        isEnM2110 = False
                        if nw_standard == 0:
                            setup = config['config']["sdhf"]
                            m21xx_para = setup["m21xx_para"]
                            isEnM2101 = m21xx_para["m2101"] == "ON" 
                            isEnM2110 = m21xx_para["m2110"] == "ON" 

                        isNotFixedPtn = ptn in "2E31,2E23,2E20,2E15,2E11,2E9,2E7,2E6,QRSS";
                        if params['serviceDisruption'] and (bert_type == 'BERT') and isNotFixedPtn:
                            self.serviceDisruptionTable(w, results, 'csv')
                        if params['G.821'] and (bert_type == 'BERT'):
                            self.g821Table(w, results, nw_standard, 'csv')
                        if params['G.828']:
                            self.g828Table(w, results, nw_standard, isLP, isTU3, 'csv')
                        if params['G.829']:
                            self.g829Table(w, results, nw_standard, 'csv')
                        if params['M.2101'] and isEnM2101:
                            self.m2101Table(w,results,nw_standard,isLP,isTU3,"csv")
                        if params['M.2110'] and isEnM2110:
                            self.m2110Table(w,results,nw_standard,isLP,isTU3,bert_type,"csv")
                    else:
                        # Write port setup
                        if self.test_mode.startswith("FC_"):
                            self.portSetupFC(w, config, 'csv')   
                        else:
                            self.portSetup(w, config, 'csv')
    
                        # Write Capture Filter
                        isThroughputLayerFC1 = False
                        if self.test_mode.startswith("FC_"):
                            if self.test_mode == 'FC_BERT':
                                bertConfig = config['config']['ether']['stFCBertConfig']
                                test_layer = get_param(bertConfig, 'testLayer')
                                if test_layer == 'FC_FC2':
                                    self.captureSetupFC(w, config, 'csv')
                                else:
                                    isThroughputLayerFC1 = True
                            else:
                                self.captureSetupFC(w, config, 'csv')
                        else:
                            self.captureSetup(w, config, 'csv')
    
                        # Write test setup
                        if self.test_mode == 'MONITOR':
                            self.monitorSetup(w, config, 'csv')
                        elif self.test_mode == 'THROUGHPUT':
                            self.bertSetup(w, config, 'csv')                   
                        elif self.test_mode == 'LOOPBACK':
                            self.loopbackSetup(w, config, 'csv')                   
                        elif self.test_mode == 'RFC2544':
                            self.rfc2544Setup(w, config,  params, 'csv')
                        elif self.test_mode == 'IP':
                            self.ipTestSetup(w, config, params, 'csv')
                        elif self.test_mode == 'Y156SAM':
                            self.y156samSetup(w, config, params, 'csv')
                        #Fibre Channel testmode
                        elif self.test_mode == 'FC_BERT':
                            self.bertSetupFC(w, config, 'csv')                   
                        elif self.test_mode == 'FC_LOOPBACK':
                            self.loopbackSetupFC(w, config, 'csv')                   
                        elif self.test_mode == 'FC_RFC2544':
                            self.rfc2544SetupFC(w, config,  params, 'csv')
                        elif self.test_mode == 'FC_B2B':
                            self.b2bSetupFC(w, config, params, 'csv')
    
                        
                        # Write test summary data
                        if params['summary']:
                            if self.test_mode == 'MONITOR':
                                self.summaryTable(w, meas_data, 'csv')     
                            elif self.test_mode == 'RFC2544':
                                self.summaryTable(w, meas_data, 'csv')       
                                self.rfc2544Summary(w, meas_data, 'csv')
                            elif self.test_mode in ('THROUGHPUT', 'LOOPBACK', 'IP'):
                                self.summaryTable(w, meas_data, 'csv')                           
                            elif self.test_mode == 'Y156SAM':
                                self.summaryTable(w, meas_data, 'csv')
                                self.y156samSummary(w, meas_data, 'csv')
                            #Fibre Channel testmode, FC_B2B has no summary page
                            elif self.test_mode in ('FC_BERT', 'FC_LOOPBACK', 'FC_RFC2544', 'FC_B2B'):
                                if isThroughputLayerFC1:
                                    self.summaryTableFC_FC1(w, meas_data, 'csv')
                                else:
                                    self.summaryTableFC(w, meas_data, 'csv')
                            self.write_log('Process Summary Table - OK.')
    
                        # Write test event log data
                        if params['eventlog']:
                            if self.test_mode in ('FC_BERT', 'FC_LOOPBACK', 'FC_RFC2544', 'FC_B2B'):
                                self.eventTableFC(w, meas_data, 'csv')
                            else:
                                self.eventTable(w, meas_data, 'csv')
                        
                        # Write test aggregate data
                        if params['aggregate']:
                            if self.test_mode == 'MONITOR':
                                self.MonitoraggregateTable(w, meas_data, 'csv')
                            elif self.test_mode == 'THROUGHPUT':
                                self.aggregateTable(w, meas_data, 'csv')
                            elif self.test_mode == 'LOOPBACK':
                                self.aggregateTable(w, meas_data, 'csv')
                            elif self.test_mode == 'RFC2544':
                                self.aggregateTable(w, meas_data, 'csv')
                            elif self.test_mode == 'IP':
                                self.aggregateTable(w, meas_data, 'csv')
                            #Fibre Channel testmode, FC_B2B has no aggregate page
                            elif self.test_mode in ('FC_BERT', 'FC_LOOPBACK', 'FC_RFC2544'):
                                if isThroughputLayerFC1:
                                    self.aggregateTableFC_FC1(w, meas_data, 'csv')
                                else:
                                    self.aggregateTableFC(w, meas_data, 'csv')
                            self.write_log('Process Agregate Table - OK.')
                        
                        # Write Stream data
                        if params['stream'] and config is not None:
                            bert_cfg = config['config']['ether']['stBertConfig'];
                            if self.test_mode == 'THROUGHPUT' and bert_cfg['testLayer'] == 'L2FRAME':
                                self.StreamResultTables(w, meas_data, 'csv')
                        
                        # Write WAN Data
                        tintf = config['config']['ether']['portConfig']['port_interface']
                        iftype = config['config']['ether']['portConfig']['xfpiface']
                        wan_support = True if self.test_mode == 'THROUGHPUT' or self.test_mode == 'RFC2544' else False
                        if wan_support and tintf == 'XFP' and iftype != 'LAN' and meas_data['result_wan'] != None:
                            self.wanResultTable(w, meas_data['result_wan'], iftype, 'csv')
                        
                        # Write RFC2544 data
                        if self.test_mode == 'RFC2544':
                            # Write Throughput Latency table
                            tputlat = meas_data['result_rfc2544']['is_latency_on'] or meas_data['result_rfc2544']['is_throughput_on']
                            if params['tputLatency'] and tputlat:                            
                                self.rfc2544LatencyTable(w, meas_data, 'csv')
                            # Write Frame Loss Table
                            if params['flTable'] == True and meas_data['result_rfc2544']['is_frameloss_on']:
                                self.rfc2544FrameLossTable(w, meas_data, 'csv')
                            # Write Back to Back Table
                            if params['bbTable'] == True and meas_data['result_rfc2544']['is_backtoback_on']:                            
                                self.rfc2544Back2BackTable(w, meas_data,'csv')
                        
                        # Write Y.156sam data
                        if self.test_mode == 'Y156SAM':
                            # Service Configuration
                            sam_setup = config['config']['ether']['stY156SAMConfig']
                            try:
                                meas_data['datatype'] = sam_setup['bwpcos']['datatype']
                            except:
                                meas_data['datatype'] = 'INFORATE'
                                
                            if params['serviceConf'] == True and sam_setup['samtype']['ensvccfg'] == 'ENABLE':
                                self.getY156samServiceConfPart1(w, meas_data, 'csv')
                                self.getY156samServiceConfPart2(w, meas_data, 'csv')
                            # Service Perfomance
                            if params['servicePerf'] == True and sam_setup['samtype']['ensvcperf'] == 'ENABLE':
                                self.getY156samServicePerfPart1(w, meas_data, 'csv')
                                self.getY156samServicePerfPart2(w, meas_data, 'csv')
    
                        #Fibre Channel testmode
                        if self.test_mode == 'FC_RFC2544':
                            # Write Throughput Latency table
                            if params['tputLatency']:                            
                                self.rfc2544LatencyTableFC(w, meas_data, 'csv')
                            # Write Frame Loss Table
                            if params['flTable'] == True:                            
                                self.rfc2544FrameLossTableFC(w, meas_data, 'csv')
                            # Write Back to Back Table
                            if params['bbTable'] == True:                            
                                self.rfc2544Back2BackTableFC(w, meas_data,'csv')
    
                        if self.test_mode == 'FC_B2B':
                            # Write B2B Result Table
                            if params['fcb2bTable']:
                                self.b2bResultTableFC(w, meas_data, 'csv')
                        # Write IP Test Data
                        if self.test_mode == 'IP':
                            self.ipTestResult(w, meas_data, params, 'csv')
                            
                        f.close()
                     
                if params['PDFfile']:
                    self.report_file_name = pdf_file_name
                    report_file_path = pdf_file_path
                    self.write_log('Report format "PDF"')
                    
                    try:   
                        self.doc = SimpleDocTemplate(report_file_path, topMargin = 0.13 * inch)
                    except:
                        message = 'Fails to open: "%s"' % report_file_path
                        self.write_log(message, 'Critical Error', sys.exc_info())
                        return {'status': 'FAIL', 'reason': message}

                    self.write_log('Generation start...')

                    story = []
                    style = styles["Normal"]

                    # Add report title
                    story.append(Spacer(1, 1.6 * inch))
                    title = '<para align=center font = Helvetica><b>RxT-TEN Measurement Report for %s</b></para>' % self.getTestmodeLabel(self.test_mode)
                    story.append(Paragraph(title, styleSheet['Heading2']))
                
                    
                    # System Information
                    self.systemInfoTable(story, meas_data, 'pdf')
                    self.write_log('Process customer data - OK.')
                    
                    # User Information
                    self.customerData(story, 'pdf')
                    self.write_log('Process customer information - OK.')
                    
                    # Comments
                    self.comments(story, 'pdf')

                    story.append(PageBreak())
                    
                    # Measurement setup data
                    if self.test_mode.startswith("FC_"):
                        self.measSetupFC(story, config, 'pdf')
                    else:
                        self.measSetup(story, config, 'pdf')
                    self.write_log('Process Meas Setup - OK.')

                    if (self.isTransport):
                        #Write measurement parameter table
                        self.sdhMeasParam(story, config, 'pdf')           
                        # Write sdh port setup
                        self.sdhPortSetup(story, config, 'pdf')
                        self.sdhInterfaceSetup(story, config, 'pdf')
                        self.sdhRxTxSettingSetup(story, config, 'pdf')
                        # Write Summary data
                        if params['summary']:
                            self.summaryTableSdh(story, meas_data, 'pdf')

                            # Write test event log data
                        if params['eventlog']:
                            self.eventTable(story, meas_data, 'pdf')
                        
                        #Write SDH result data
                        #get_param_format
                        
                        results = meas_data['result_sdh']['result']
                        nw_standard = self.getNwStandard(meas_data)
                        isLP = self.isLP(meas_data)
                        isTU3 = self.isTU3(meas_data)
                        #print "isLP=%d isTU3=%d" %(isLP, isTU3)
                        if params['Signal']:
                            self.signalTable(story, results, 'pdf')
                        if params['sdh']:
                            self.sdhTable(story, results, nw_standard, isLP, isTU3, 'pdf')
                        ptn="None"
                        if config['config']['rx_standard'] == 'SDH':
                            bert_type = config['config']['stm']['bert']['rx_pattern']['mode']
                            ptn       = config['config']['stm']['bert']['rx_pattern']['type']
                        elif config['config']['rx_standard'] == 'SONET':
                            bert_type = config['config']['sonet']['bert']['rx_pattern']['mode']
                            ptn       = config['config']['sonet']['bert']['rx_pattern']['type']
                        else:
                            bert_type = config['config']['otn']['bert']['rx_pattern']['mode']
                            
                        isEnM2101 = False
                        isEnM2110 = False
                        if nw_standard == 0:
                            setup = config['config']["sdhf"]
                            m21xx_para = setup["m21xx_para"]
                            isEnM2101 = m21xx_para["m2101"] == "ON" 
                            isEnM2110 = m21xx_para["m2110"] == "ON" 

                        isNotFixedPtn = ptn in "2E31,2E23,2E20,2E15,2E11,2E9,2E7,2E6,QRSS";
                        if params['serviceDisruption'] and (bert_type == 'BERT') and isNotFixedPtn:
                            self.serviceDisruptionTable(story, results, 'pdf')
                        if params['G.821'] and (bert_type == 'BERT'):
                            self.g821Table(story, results, nw_standard, 'pdf')
                        if params['G.828']:
                            self.g828Table(story, results, nw_standard, isLP, isTU3, 'pdf')
                        if params['G.829']:
                            self.g829Table(story, results, nw_standard, 'pdf')
                        if params['M.2101'] and isEnM2101:
                            self.m2101Table(story,results,nw_standard,isLP,isTU3,"pdf")
                        if params['M.2110'] and isEnM2110:
                            self.m2110Table(story,results,nw_standard,isLP,isTU3,bert_type,"pdf")
                    else:
                        # Write port setup
                        if self.test_mode.startswith("FC_"):
                            self.portSetupFC(story, config, 'pdf')
                        else:
                            self.portSetup(story, config, 'pdf')
                        self.write_log('Process Port Setup - OK.')
    
                        # Write Capture Filter
                        isThroughputLayerFC1 = False
                        if self.test_mode.startswith("FC_"):
                            if self.test_mode == 'FC_BERT':
                                bertConfig = config['config']['ether']['stFCBertConfig']
                                test_layer = get_param(bertConfig, 'testLayer')
                                if test_layer == 'FC_FC2':
                                    self.captureSetupFC(story, config, 'pdf')
                                else:
                                    isThroughputLayerFC1 = True
                            else:
                                self.captureSetupFC(story, config, 'pdf')
                        else:
                            self.captureSetup(story, config, 'pdf')
    
                        # Write test setup
                        if self.test_mode == 'MONITOR':
                            self.monitorSetup(story, config, 'pdf')
                            self.write_log('Process Monitor Setup - OK.')
                        elif self.test_mode == 'THROUGHPUT':
                            self.bertSetup(story, config, 'pdf')
                            self.write_log('Process Bert Setup - OK.')
                        elif self.test_mode == 'LOOPBACK':
                            self.loopbackSetup(story, config, 'pdf')
                            self.write_log('Process Loopbeck Setup - OK.')
                        elif self.test_mode == 'RFC2544': 
                            self.rfc2544Setup(story, config, params, 'pdf')
                            self.write_log('Process RFC2544 Setup - OK.')
                        elif self.test_mode == 'IP':                
                            self.ipTestSetup(story, config, params, 'pdf')          
                            self.write_log('Process IP Test Setup - OK.') 
                        elif self.test_mode == 'Y156SAM':
                            self.y156samSetup(story, config, params, 'pdf')
                        #Fibre Channel testmode
                        elif self.test_mode == 'FC_BERT':
                            self.bertSetupFC(story, config, 'pdf')
                        elif self.test_mode == 'FC_LOOPBACK':                
                            self.loopbackSetupFC(story, config, 'pdf')
                        elif self.test_mode == 'FC_RFC2544':                
                            self.rfc2544SetupFC(story, config, params, 'pdf')
                        elif self.test_mode == 'FC_B2B':                
                            self.b2bSetupFC(story, config, params, 'pdf')
    
                        # Write Summary data
                        if params['summary']:
                            if self.test_mode == 'MONITOR':
                                self.summaryTable(story, meas_data, 'pdf')
                            elif self.test_mode == 'RFC2544':
                                self.summaryTable(story, meas_data, 'pdf')
                                self.rfc2544Summary(story, meas_data, 'pdf')
                            elif self.test_mode in ('THROUGHPUT', 'LOOPBACK'):                                            
                                self.summaryTable(story, meas_data, 'pdf')
                            elif self.test_mode == 'Y156SAM':
                                self.summaryTable(story, meas_data, 'pdf')
                                self.y156samSummary(story, meas_data, 'pdf')
                            #Fibre Channel testmode, FC_B2B has no summary page
                            elif self.test_mode in ('FC_BERT', 'FC_LOOPBACK', 'FC_RFC2544', 'FC_B2B'):
                                if isThroughputLayerFC1:
                                    self.summaryTableFC_FC1(story, meas_data, 'pdf')
                                else:
                                    self.summaryTableFC(story, meas_data, 'pdf')
                            self.write_log('Process Summary Table - OK.')
    
                        # Write test event log data
                        if params['eventlog']:
                            if self.test_mode in ('FC_BERT', 'FC_LOOPBACK', 'FC_RFC2544', 'FC_B2B'):
                                self.eventTableFC(story, meas_data, 'pdf')
                            else:
                                self.eventTable(story, meas_data, 'pdf')
                            self.write_log('Process Event Table - OK.')
                        
                        # Write Aggregate data
                        if params['aggregate']:             
                            if self.test_mode == 'MONITOR':
                                self.MonitoraggregateTable(story, meas_data, 'pdf')
                            elif self.test_mode == 'THROUGHPUT':
                                self.aggregateTable(story, meas_data, 'pdf')
                            elif self.test_mode == 'LOOPBACK':
                                self.aggregateTable(story, meas_data, 'pdf')
                            elif self.test_mode == 'RFC2544':
                                self.aggregateTable(story, meas_data, 'pdf')
                            elif self.test_mode == 'IP':                          
                                self.aggregateTable(story, meas_data, 'pdf')
                            #Fibre Channel testmode, FC_B2B has no aggregate page
                            elif self.test_mode in ('FC_BERT', 'FC_LOOPBACK', 'FC_RFC2544'):
                                if isThroughputLayerFC1:
                                    self.aggregateTableFC_FC1(story, meas_data, 'pdf')
                                else:
                                    self.aggregateTableFC(story, meas_data, 'pdf')
                            self.write_log('Process Agregate Table - OK.')
         
                        # Write Stream data
                        if params['stream'] and config is not None:
                            bert_cfg = config['config']['ether']['stBertConfig'];
                            if self.test_mode == 'THROUGHPUT' and bert_cfg['testLayer'] == 'L2FRAME':
                                self.StreamResultTables(story, meas_data, 'pdf')
                                self.write_log('Process Stream Table - OK.')
                        
                        # Write WAN Data
                        tintf = config['config']['ether']['portConfig']['port_interface']
                        iftype = config['config']['ether']['portConfig']['xfpiface']
                        wan_support = True if self.test_mode == 'THROUGHPUT' or self.test_mode == 'RFC2544' else False
                        if wan_support and tintf == 'XFP' and iftype != 'LAN' and meas_data['result_wan'] != None:
                            self.wanResultTable(story, meas_data['result_wan'], iftype, 'pdf')
                        
                        # Write RFC2544 data
                        if self.test_mode == 'RFC2544':
                            # Write Throughput Latency table
                            tputlat = meas_data['result_rfc2544']['is_latency_on'] or meas_data['result_rfc2544']['is_throughput_on']
                            if params['tputLatency'] and tputlat :                                    
                                self.rfc2544LatencyTable(story, meas_data, 'pdf')
                                self.write_log('Process Latency Table - OK.')
                            # Write Frame Loss Table
                            if params['flTable'] and meas_data['result_rfc2544']['is_frameloss_on']:                            
                                self.rfc2544FrameLossTable(story, meas_data, 'pdf')
                                self.write_log('Process Frame Loss Table - OK.')
                            # Write Back to Back Table
                            if params['bbTable'] and meas_data['result_rfc2544']['is_backtoback_on']:                            
                                self.rfc2544Back2BackTable(story, meas_data, 'pdf')
                                self.write_log('Process Back to Back Table - OK.')
                            # Write Throughput Chart
                            if params['tputChart'] and meas_data['result_rfc2544']['is_throughput_on']:                            
                                self.throughPutChart(story, meas_data)
                                self.write_log('Process Throughput Chart - OK.')
                            # Write Frame Loss Chart
                            if params['flChart'] and meas_data['result_rfc2544']['is_frameloss_on']:                            
                                self.frameLossChart(story, meas_data)
                                self.write_log('Process Frame Loss Chart - OK.')
      
                        # Write Y.156sam data
                        if self.test_mode == 'Y156SAM':
                            # Service Configuration
                            sam_setup = config['config']['ether']['stY156SAMConfig']
                            try:
                                meas_data['datatype'] = sam_setup['bwpcos']['datatype']
                            except:
                                meas_data['datatype'] = 'INFORATE'
    
                            try:
                                if params['serviceConf'] == True and sam_setup['samtype']['ensvccfg'] == 'ENABLE':
                                    self.getY156samServiceConfPart1(story, meas_data, 'pdf')
                                    self.getY156samServiceConfPart2(story, meas_data, 'pdf')
                            except:
                                print sys.exc_info()
    
                           # Service Perfomance
                            try:
                                if params['servicePerf'] == True and sam_setup['samtype']['ensvcperf'] == 'ENABLE':
                                    self.getY156samServicePerfPart1(story, meas_data, 'pdf')
                                    self.getY156samServicePerfPart2(story, meas_data, 'pdf')
                            except:
                                print sys.exc_info()
                                
                        #Fibre Channel testmode
                        if self.test_mode == 'FC_RFC2544':
                            # Write Throughput Latency table
                            if params['tputLatency']:
                                self.rfc2544LatencyTableFC(story, meas_data, 'pdf')
                            # Write Frame Loss Table
                            if params['flTable']:
                                self.rfc2544FrameLossTableFC(story, meas_data, 'pdf')
                            # Write Back to Back Table
                            if params['bbTable']:
                                self.rfc2544Back2BackTableFC(story, meas_data, 'pdf')
                            # Write Throughput Chart
                            if params['tputChart']:
                                self.throughPutChartFC(story, meas_data)
                            # Write Frame Loss Chart
                            if params['flChart']:
                                self.frameLossChartFC(story, meas_data)
    
                        if self.test_mode == 'FC_B2B':
                            # Write B2B Result Table
                            if params['fcb2bTable']:                            
                                self.b2bResultTableFC(story, meas_data, 'pdf')
    
                        # Write IP Test Data
                        if self.test_mode == 'IP':
                            self.ipTestResult(story, meas_data, params, 'pdf')
                    #End of if for Transport
                    
                    # Build the document
                    self.write_log('Start build document...')                    
                    try:   
                        self.doc.build(story, onFirstPage = self.myFirstPage, \
                                       onLaterPages = self.myLaterPages, canvasmaker = NumberedCanvas)
                        self.report_status = 'COMPLETE'
                    except:
                        self.report_status = 'FAIL'
                        message = 'crte_results_report(): fails to write: "%s"' % report_file_path
                        self.write_log(message, 'Error', sys.exc_info())                   
                    self.write_log('End build document...')
                #Endif of PDF
        
        except:            
            self.write_log('', 'Critical error', sys.exc_info())        
            self.report_status = 'FAIL'

        if self.report_status == 'FAIL':            
            return {'status': self.report_status, 'reason': 'Failed to Generate: %s %s' % (self.report_file_name, self.failReason)}
        else:        
            return {'status': self.report_status, 'reason': 'Report Generated for -> %s' % self.report_file_name}

    def createPdfTable(self, lst, header, table, style=[], colwidths = None):
        if colwidths == None:
            colwidths = [3.525 * inch, 3.525 * inch]
        maxLen = len(table)
        style.extend(\
            [
                ('BOX', (0, 0), (-1, -1), 1, colors.grey),
                ('BOX', (0, 0), (0, -1), 1, colors.grey),
                ('SIZE', (0, 0), (-1, -1), 10),
                ('FONT', (0, 0), (-1, -1), 'Helvetica'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ])
        if (header.startswith("Summary Data ") == False):
            if maxLen > 1:
                altCol = [Color(.92, .92, .92), Color(1, 1, 1)]
                n = 0
                for row in range(maxLen):
                    style.append(('BACKGROUND', (0, row), (-1, row), altCol[n]))
                    if n == 0:
                        n += 1
                    else: n -= 1

        if maxLen == 1 and self.test_mode != 'MONITOR' and (not self.test_mode in ('FC_BERT', 'FC_LOOPBACK', 'FC_RFC2544', 'FC_B2B')):
            tw = len(table[0])            
            no_data_row = [''] * tw            
            no_data_row[0] = 'No Data Available'
            style.append( ('SPAN',(0,1),(tw-1,1)) )
            table.append(no_data_row)

        obj = Table(table, colwidths, None, style)
        lst.append(Paragraph('<para spaceAfter = 2 leftIndent = -30><font name = Helvetica size = 12>%s</font></para>'%header, styleSheet['h2']))
        lst.append(obj)
        lst.append(Spacer(1, 0.2 * inch))
        del style[:]

    def createCsvTable(self, w, header, table, style=[], colwidths=None):
        w.writerow('')
        w.writerow(['#%s'%header])
        for row in table:
            w.writerow(row)

    def ipTestResult(self, fd, meas_data, params, format):
        try:
            results = meas_data['result_iptest']
            res_type = results['ip_test_type']
        except:
            self.write_log('IPTest Result data not found!', 'Error', sys.exc_info())
            return 

        if format == 'pdf':
            makeTable = self.createPdfTable
        elif format == 'csv':
            makeTable = self.createCsvTable    
        
        #if 'RTRV_DHCP_RESULT' in results:
        #    dhcp_table = self.getIpDhcpData(results,format)
        #    makeTable(fd, "DHCP Result", dhcp_table)

        if params['echoLog']:
            echo_table = self.getIpEchoData(results, format)
            makeTable(fd, "Echo Log", echo_table)

        if res_type == 'PING' and params['ping']:
            ping_table = self.getIpPingData(results, format)
            makeTable(fd, "Ping Result", ping_table)
            
        elif res_type == 'TRACEROUTE': # and params['traceRoute']:
            trace_table = self.getIpTraceData(results, format)
            makeTable(fd, "Trace Route Result", trace_table)
            
        elif res_type == 'FTP':
            if 'ftp' not in params or params['ftp']:
                ftp_table = self.getIpFtpData(results, format)
                makeTable(fd, "FTP Result", ftp_table)
            
        elif res_type == 'HTTP':
            if 'http' not in params or params['http']:
                http_table = self.getIpHttpData(results, format)
                makeTable(fd, "HTTP Result", http_table)

    '''
    def getIpDhcpData(self, results,format):                        
        nvp = \
            [
                ('Status',self.get_result_param(results,'RTRV_DHCP_RESULT','dhcpst')),
                ('Local IP',self.get_result_param(results,'RTRV_DHCP_RESULT','lip')),
                ('Netmask',self.get_result_param(results,'RTRV_DHCP_RESULT','nm')),
                ('Gateway',self.get_result_param(results,'RTRV_DHCP_RESULT','gw')),
                ('DNS',self.get_result_param(results,'RTRV_DHCP_RESULT','dns')),
                ('Lease Time',self.get_result_param(results,'RTRV_DHCP_RESULT','ltime'))
            ]
        
        detail_count = self.get_result_param(results, 'RTRV_DHCP_RESULT','dinfocnt',0)
        
        for x in range (1,detail_count+1):
            nvp.append( ('Detail Info '+str(x),self.get_result_param(results,'RTRV_DHCP_RESULT','dinfo'+str(x))) )            
        
        table = []
        if format == 'pdf':
            for n,v in nvp:
                table.append([n,v])
        else:
            names = []
            values = []
            for n,v in nvp:
                names.append("'"+n+"'")
                values.append(v)
            table.append(names)
            table.append(values)
        
        return table'''

    def getIpEchoData(self, meas_data, format):        
        try:
            results = meas_data['echo']
        except:
            self.write_log('IPTest Echo Result data not found!', 'Error', sys.exc_info())
            return
        
        num_ip = get_param(results, 'num_ip', 0)
        
        table = []
        if format == 'pdf':
            table.append(['Source IP', 'Echo Count'])
        else:
            table.append(["Source IP", "Echo Count"])
        
        i = 0
        while i < num_ip:
            i += 1
            echo = results['stats'][i - 1]
            row = [get_param(echo, 'ip', INA), get_param(echo, 'cnt')]
            table.append(row)
            
        return table

    def getIpPingData(self, meas_data, format):
        try:
            results = meas_data['result']
        except:
            self.write_log('IPTest Ping Result data not found!', 'Error', sys.exc_info())
            return
        
        table = []
        num_dest = get_param(results, 'ping_cnt', 0)

        if format == 'pdf':
            table.append([  'IP Address',                            
                            'Sent\nPings',
                            'Received\nPings',
                            'Lost\nPings',
                            'Unreachable',                            
                            'TTL\nExceed',
                            'Round Trip Delay (ms)\nCur | Avg | Min | Max',])
            i = 0;
            while i < num_dest:                
                ping = results['stats'][i]
                row = \
                    [
                        get_param(ping, 'dest', INA),
                        get_param(ping, 'sent'),
                        get_param(ping, 'recv'),
                        get_param(ping, 'lost'),
                        get_param(ping, 'unreach'),                        
                        get_param(ping, 'ttl_exceed'),
                        "%s / %s / %s / %s" % (get_param(ping, 'rtd_cur'), get_param(ping, 'rtd_avg'),
                                               get_param(ping, 'rtd_min'), get_param(ping, 'rtd_max'))                        
                    ]
                table.append(row)
                i += 1
        else:
            table.append([  "IP Address",
                            "Sent\nPings",
                            "Received\nPings",
                            "Lost\nPings",
                            "Unreachable",                            
                            "TTL\nExceed",
                            "Round Trip Delay (ms)\nCur | Avg | Min | Max",])
            i = 0;            
            while i < num_dest:                
                ping = results['stats'][i]
                row = \
                    [
                        get_param(ping, 'dest', INA),
                        get_param(ping, 'sent'),
                        get_param(ping, 'recv'),
                        get_param(ping, 'lost'),
                        get_param(ping, 'unreach'),                        
                        get_param(ping, 'ttl_exceed'),
                        "%s / %s / %s / %s" % (get_param(ping, 'rtd_cur'), get_param(ping, 'rtd_avg'),
                                               get_param(ping, 'rtd_min'), get_param(ping, 'rtd_max'))                        
                    ]
                table.append(row)
                i += 1
    
        return table

    def getIpTraceData(self, meas_data, format):
        try:
            results = meas_data['result']
        except:
            self.write_log('IPTest Trace Result data not found!', 'Error', sys.exc_info())
            return
        
        table = []
        total_hops = get_param(results, 'hop_cnt', 0)
        
        if total_hops == 0:
            #Failed Trace Route, so display at least 1 row
            total_hops = 1
    
        if format == 'pdf':
            table.append(['Status','Destination','Hop Number','IP Address','Delay (ms)'])
        else:
            table.append(["Status","Destination","Hop Number","IP Address","Delay (ms)"])
        
        i = 0;
        st = get_param(results,'status')
        while i < total_hops:
            trace = results['stats'][i]
            ip = get_param(trace,'ip')
            row = \
                [
                    (st if ip != 0 else 'FAIL'),
                    get_param(results,'dest_ip', INA),
                    i+1,
                    get_param(trace,'ip', INA),
                    get_param(trace,'delay')
                ]
            table.append(row)
            i += 1    
        return table
        
    def getIpFtpData(self, meas_data, format):
        try:
            results = meas_data['result']
        except:
            self.write_log('IPTest FTP Result data not found!', 'Error', sys.exc_info())
            return
        
        nvp = \
            [
                ('Test Status', get_param(results, 'status')),
                ('FTP Server IP', get_param(results, 'server_ip', INA)),
                ('URL', get_param(results, 'hostname')),
                ('File Name', get_param(results, 'filename')),
                ('Transfer Type', get_param(results, 'xfer_type')),
                ('Transferred Bytes', get_param(results, 'xfer_byte')),
                ('Transfer Time (ms)', get_param(results, 'xfer_time')),
                fbps('Average Transfer Rate (%s)', get_param(results, 'xfer_rate')),
                fbps('Minimum Transfer Rate (%s)', get_param(results, 'xfer_rate_min')),
                fbps('Maximum Transfer Rate (%s)', get_param(results, 'xfer_rate_max'))
            ]                
        
        table = []
        if format == 'pdf':
            for n, v in nvp:
                table.append([n,v])
        else:
            table = nvp
        
        return table
        
    def getIpHttpData(self, meas_data, format):
        try:
            results = meas_data['result']
        except:
            self.write_log('IPTest HTTP Result data not found!', 'Error', sys.exc_info())
            return
    
        nvp = \
            [
                ('Test Status', get_param(results, 'status')),
                ('HTTP Server IP', get_param(results, 'server_ip', INA)),
                ('URL', get_param(results, 'hostname')),                
                ('Transferred Bytes', get_param(results, 'xfer_byte')),
                ('Transfer Time (ms)', get_param(results, 'xfer_time')),
                fbps('Average Transfer Rate (%s)', get_param(results, 'xfer_rate')),
                fbps('Minimum Transfer Rate (%s)', get_param(results, 'xfer_rate_min')),
                fbps('Maximum Transfer Rate (%s)', get_param(results, 'xfer_rate_max'))
            ]
    
        table = []
        
        if format == 'pdf':
            for n, v in nvp:
                table.append([n, v])
        else:
            table = nvp
    
        return table
    
        
    def ipTestSetup(self, fd, config, params, format):
        
        try:
            setup = config['config']['ether']['stIpTestConfig']
        except:
            self.write_log('IPTest setup data not found!', 'Error', sys.exc_info())
            return         
        
        # Set the Table Creation function
        if format == 'pdf':
            makeTable = self.createPdfTable
        elif format == 'csv':
            makeTable = self.createCsvTable
       
        iptest_type = get_param(setup, 'iptest_type')

        # Make IP Setup Table
        ip_setup_table = self.getIpConfig(setup,format)
        makeTable(fd,'IP Setup',ip_setup_table)
        
        # Make VLAN Setup Table
        ip_vlan_table = self.getIpVlanConfig(setup,format)
        if get_param(setup['ip_config'], 'vlan_num') > 0:
            makeTable(fd,'VLAN Setup',ip_vlan_table)
               
        # Make PING Setup Table
        if iptest_type == 'PING':
            ip_ping_table = self.getIpPingConfig(setup,format)
            makeTable(fd,'Ping Setup',ip_ping_table)
        
        # Make Traceroute Setup Table
        if iptest_type == 'TRACEROUTE' : 
            ip_traceroute_table = self.getIpTracerouteConfig(setup,format)
            makeTable(fd,'Traceroute Setup',ip_traceroute_table)
        
        # Make FTP Setup Table
        if iptest_type == 'FTP':
            if 'ftp' not in params or params['ftp']:
                ip_ftp_table = self.getIpFtpConfig(setup,format)
                makeTable(fd,'FTP Setup',ip_ftp_table)
        
        # Make HTTP Setup Table
        if iptest_type == 'HTTP':
            if 'http' not in params or params['http']:
                ip_http_table = self.getIpHttpConfig(setup,format)
                makeTable(fd,'HTTP Setup',ip_http_table)

    def getIpConfig(self, setup, format): 
        mode = get_param(setup['ip_config'], 'ip_type')
        ip = get_param(setup['ip_config'],'local_ipv4_addr', INA)
        gateway = get_param(setup['ip_config'],'gw_ipv4_addr', INA)
        subnet = get_param(setup['ip_config'],'netmask_ipv4', INA)
        dns = get_param(setup['ip_config'],'dns_ipv4_addr', INA)
        
        nvp = \
            [
                ('IP Test Type', setup['iptest_type']),
                ('Source IP Mode',mode),
                ('Source IP',ip),
                ('Source Gateway',gateway),
                ('Source Subnet Mask',subnet),
                ('Source DNS',dns)
            ]
    
        table = []
        if format == 'pdf':
            for n,v in nvp:
                table.append([n,v])                
        else:
            table = nvp
        
        return table
            
    def getVlanTable(self, vlan_setup, num_vlans):
        stream_vlan_table = []
        names = ["VLAN", "TPID", "Priority", "CFI", "ID"]
        stream_vlan_table.append(names)
        for x in range(1,num_vlans+1):
            vlan = vlan_setup[x-1]
            if x == num_vlans :
                tpid = int_to_hex(33024, 4, True);
            else :
                tpid = int_to_hex(vlan['tpid'], 4, True)
            values = \
                [
                    x,
                    tpid,
                    get_param(vlan,'priority'),
                    get_param(vlan,'cfi', ENDI),
                    get_param(vlan,'vid'),
                ]
            stream_vlan_table.append(values)
        return stream_vlan_table

    def getIpVlanConfig(self, setup, format):
        vlans = setup['ip_config']['VlanCfg']
        table = []
        if setup['ip_config']['vlan_enable'] == 'FALSE':
            return table
        num_vlans = setup['ip_config']['vlan_num']
        if num_vlans < 1:
           return table
 
        table = self.getVlanTable(vlans, num_vlans)
        return table
        
    def getIpPingConfig(self, setup, format):
        num_pings = get_param(setup['ping_config'],'num_of_ping')
        if num_pings ==  0:
            num_pings = 'Continuous'
            
        nvp = \
            [
                ('Ping Rate (per second)',get_param(setup['ping_config'], 'ping_rate')),
                ('Frame Length',get_param(setup['ping_config'], 'pkt_size')),
                ('# of Ping Packets',num_pings),
                ('Time to Live',get_param(setup['ping_config'], 'ping_ttl')),
                ('Time Out (seconds)',get_param(setup['ping_config'], 'ping_timeout')),
            ]
        
        num_dest = setup['ping_config']['num_dest']       
        for x in range(1,num_dest+1):
            nvp.append( ('IP Destination - '+str(x),get_param(setup['ping_config'],'dest'+str(x))) )

        table = []
        if format == 'pdf':
            for n,v in nvp:
                table.append([n,v])
        else:            
            table = nvp
        return table
        
    def getIpTracerouteConfig(self, setup, format):
    
        nvp = \
            [
                ('Maximum Hops',get_param(setup['tracert_config'],'max_hop')),
                ('Time Out (seconds)',get_param(setup['tracert_config'],'timeout')),
                ('Destination IP/URL',get_param(setup['tracert_config'],'dest', ITS))
            ]
               
        table = []
        if format == 'pdf':
            for n,v in nvp:
                table.append([n,v])
        else:
            table = nvp
        
        return table
        
    def getIpFtpConfig(self, setup, format):
        nvp = \
            [
                ('FTP Type',get_param(setup['ftp_config'],'direction')),
                ('Server Address',get_param(setup['ftp_config'],'dest', ITS)),
                ('User Name',get_param(setup['ftp_config'],'user_name', ITS)),
                ('Password',get_param(setup['ftp_config'],'passwd', ITS)),
                ('File Name',get_param(setup['ftp_config'],'file_name', ITS)),
                ('File Size',get_param(setup['ftp_config'],'file_size'))
            ]
    
        table = []
        if format == 'pdf':
            for n,v in nvp:
                table.append([n,v])
        else:
            table = nvp
        
        return table
        
    def getIpHttpConfig(self, setup, format):
        nvp = \
            [
                ('Destination',get_param(setup['http_config'],'dest', ITS))
            ]
    
        table = []
        if format == 'pdf':
            for n,v in nvp:
                table.append([n,v])
        else:
            table = nvp
        
        return table

    def y156samSetup(self, fd, config, params, format):        
        # Get Command List For Y.156sam
        print '[reportGenerator] y156samSetup'
        try:
            setup = config['config']['ether']['stY156SAMConfig']
        except:
            self.write_log('RFC2544 setup data not found!', 'Error', sys.exc_info())
            return
             
        # Set the Table Creation function
        if format == 'pdf':
            makeTable = self.createPdfTable
        elif format == 'csv':
            makeTable = self.createCsvTable
        else:
            self.log.debug("Format Not Specified, Exiting")
            return
        # Make IntelliSAM Setup Table                
        setup_table = self.getY156SAMSetupConfig(setup, format)
        makeTable(fd, 'IntelliSAM Setup', setup_table)   
        
        # Make Sequence Table                
        #seq_table = self.getY156SAMTestSeq(setup, format)
        #makeTable(fd, 'Service Config. Test Seq.', seq_table)
        
        # Make BWP Table
        bwp_table = self.getY156SAMBWPConfig(setup, format)
        makeTable(fd, 'BWP Setup', bwp_table)
        
        # Make CoS Table
        cos_table = self.getY156SAMCoSConfig(setup, format)
        makeTable(fd, 'Service Acceptance Criteria Setup', cos_table)
        
        #Make Traffic Shape Table
        traffic_table_ramp = self.getY156SAMTrafficRampConfig(setup, format)
        makeTable(fd, 'Traffic Ramp Setup', traffic_table_ramp)
        traffic_table_burst = self.getY156SAMTrafficBurstConfig(setup, format)
        makeTable(fd, 'Traffic Burst Setup', traffic_table_burst)
        
        service_table = self.getY156SAMServiceTableConfig(setup, format)
        makeTable(fd, 'Service Table Setup', service_table)

        snum = setup['evcmap']['nevc']
        cm = setup['bwpcos']['bwp'][0]['cm']
        if cm == 'ENABLE':
            snum *= 2
            
        for sno in range(1, snum + 1):
            # Get Stream Setup Booleans
            # BWP/CoS Number Setup
            try:
                if cm == 'ENABLE':
                    bwpcosno = setup['crbwpcosno']
                else :
                    bwpcosno = setup['ncrbwpcosno']
            except:
                bwpcosno = setup['bwpcosno']
            stream_bwp_cos_table = self.getY156SAMStreamBWPCOSConfig(bwpcosno, format, sno)
            makeTable(fd, 'Stream-' +str(sno)+ ' BWP/SAC Number',stream_bwp_cos_table)
 
            streamTable = setup['streamTable'][sno-1]
            layerConfig = streamTable['layerConf']
            vlan_on = get_param(layerConfig, 'enVlan')
            mpls_on = get_param(layerConfig, 'enMpls')
            ip_on = get_param(layerConfig, 'layer234Type')

            # Stream Frame Setup
            stream_frame_mac_table = self.getY156SAMStreamFrameMacConfig(streamTable, format, sno)
            makeTable(fd, 'Stream-' +str(sno)+ ' Setup', stream_frame_mac_table)
    
            # Stream VLAN Setup
            if vlan_on != 0:
                stream_vlan_table = self.getY156SAMStreamVlanConfig(streamTable, format, sno)
                makeTable(fd, 'Stream-' +str(sno)+ ' VLAN Setup', stream_vlan_table)        
            
            # Stream MPLS Setup
            if mpls_on != 0:
                stream_mpls_table = self.getY156SAMStreamMplsConfig(streamTable, format, sno)
                makeTable(fd, 'Stream-' +str(sno)+ ' MPLS Setup', stream_mpls_table)
                
            # Stream IP Setup
            if ip_on == 'IP' or ip_on == 'TCP' or ip_on == 'UDP':
                stream_ip_table = self.getY156SAMStreamIpConfig(streamTable, format, sno)
                makeTable(fd, 'Stream-' +str(sno)+ ' IP Setup', stream_ip_table)            
    
            # UDP Setup
            if ip_on == 'UDP':
                stream_udp_table = self.getY156SAMStreamUdpConfig(streamTable, format, sno)
                makeTable(fd, 'Stream-' +str(sno)+ ' UDP Setup', stream_udp_table)
    
            # TCP Setup
            if ip_on == 'TCP':
                stream_tcp_table = self.getY156SAMStreamTcpConfig(streamTable, format, sno)
                makeTable(fd, 'Stream-' +str(sno)+ ' TCP Setup', stream_tcp_table)
        
            # Payload Setup
            stream_payload_table = self.getY156SAMPayloadConfig(streamTable, format, sno)
            makeTable(fd, 'Stream-' +str(sno)+ ' Payload Setup', stream_payload_table)
            
       
    def getY156SAMSetupConfig(self, setup, format):
        cirOn = 'ON' if setup['sequence'][0] == 'ENABLE' else 'OFF'
        eirOn = 'ON' if setup['sequence'][1] == 'ENABLE' else 'OFF'
        TPOn =  'ON' if setup['sequence'][2] == 'ENABLE' else 'OFF'
        cbsOn = 'ON' if setup['sequence'][3] == 'ENABLE' else 'OFF'
        ebsOn = 'ON' if setup['sequence'][4] == 'ENABLE' else 'OFF'
        svcconf = 'ON' if setup['samtype']['ensvccfg'] == 'ENABLE' else 'OFF'
        svcperf = 'ON' if setup['samtype']['ensvcperf'] == 'ENABLE' else 'OFF'

        nvp = [ ('Service Configuration Test',svcconf) ]
        if svcconf == 'ON': 
            nvp.append(('CIR', cirOn))
            nvp.append(('EIR', eirOn))
            nvp.append(('Traffic Policing', TPOn))
            nvp.append(('CBS', cbsOn))
            nvp.append(('EBS', ebsOn))

        nvp.append(('Service Performance Test', svcperf))
        if svcperf == 'ON':
            perfdur = {'CONTINUOUS':'CONTINUOUS',
                   '15MIN':'15 MINUTES',
                   '2HOURS':'2 HOURS',
                   '24HOURS':'24 HOURS',
                   'USER':'USER'
                   }[setup['perfdur']]
            nvp.append(('Service Perf. Test Duration', perfdur))
            if perfdur == 'USER':
                duration = str(setup['duration']) + ' MINUTES'
                nvp.append(('Duration(Minutes)', duration))

        setup_table = []        
        if format == 'pdf':
            for n, v in nvp:
                setup_table.append([n,v])
        else:
            setup_table = nvp
                 
        return setup_table   

    def getY156SAMTestSeq(self, setup, format):
        nvp = \
        [
            ('CIR', ('ON' if setup['sequence'][0] == 'ENABLE' else 'OFF')),
            ('EIR', ('ON' if setup['sequence'][1] == 'ENABLE' else 'OFF')),
            ('Traffic Policing',('ON' if setup['sequence'][2] == 'ENABLE' else 'OFF')),
            ('CBS', ('ON' if setup['sequence'][3] == 'ENABLE' else 'OFF')),
            ('EBS', ('ON' if setup['sequence'][4] == 'ENABLE' else 'OFF'))
        ]                             
        seq_table = []        
        if format == 'pdf':
            for n, v in nvp:
                seq_table.append([n,v])
        else:
            seq_table = nvp
                 
        return seq_table   
 
    def getY156SAMBWPConfig(self, setup, format):
        bwp_setup = setup['bwpcos']['bwp']
        bwp_table = []
        bwp_table.append(['#', 'CIR (kbps)', 'EIR (kbps)', 'CBS (Bytes)', 'EBS (Bytes)', 'CM', 'Data Type'])
        cm = 'ON' if bwp_setup[0]['cm'] == 'ENABLE' else 'OFF'
        try:
            datatype = {'INFORATE':'Information Rate', 
                        'LINERATE':'Line Rate'
                        }[setup['bwpcos']['datatype']]
        except:
            datatype = 'Information Rate'
            
        for x in range(0, 16):
            row =  \
            [
                x+1,
                curnum_to_string(bwp_setup[x]['cir'], True),
                curnum_to_string(bwp_setup[x]['eir'], True),
                curnum_to_string(bwp_setup[x]['cbs'], True),
                curnum_to_string(bwp_setup[x]['ebs'], True),
                cm,
                datatype
            ]                    
            bwp_table.append(row)
        return bwp_table
 
    def getY156SAMCoSConfig(self, setup, format):
        cos_setup = setup['bwpcos']['cos']
        cos_table = []
        FDV_string = Paragraph('<para><font>FDV (&#181;s)</font></para>', styleSheet['Normal']).getPlainText()
        RTD_string = Paragraph('<para><font>RTD (&#181;s)</font></para>', styleSheet['Normal']).getPlainText()

        cos_table.append(['#', 'Label', FDV_string, RTD_string, 'Frame Loss (%)', 'Availability (%)', 'FLR Limit for Avail.(%)'])
               
        for x in range(0, 20):
            coslabel = cos_setup[x]['coslabel']
            if coslabel == 'USER':
                coslabel = cos_setup[x]['userlabel']
            row =  \
            [
                x+1,
                coslabel,
                curnum_to_string(cos_setup[x]['fdv'], True),
                curnum_to_string(cos_setup[x]['rtfd'], True),
                get_param_float(cos_setup[x], 'floss', '1.0000000', 7),
                get_param_float(cos_setup[x], 'avail', '50.00000', 5),
                get_param_float(cos_setup[x], 'flra', '50.00000', 5)
            ]                    
            cos_table.append(row)
        return cos_table
   
    def getY156SAMTrafficRampConfig(self, setup, format):
        ramp_setup = setup['trafficShape']['ramp']
        div_factor = 1000000
        nvp = \
        [
            #('Ramp repeat', self.get_cmd_param(setup, 'SET-Y156SAM-TRAFFIC', 'repeat')),
            ('Start Bandwidth (%)', ramp_setup['startBandwidth']/div_factor),
            ('Stop Bandwidth (%)', ramp_setup['stopBandwidth']/div_factor),
            ('Step Bandwidth (%)', ramp_setup['stepSize']/div_factor),
            ('Step Duration (s)', ramp_setup['stepDuration']),
        ]       
        traffic_table_ramp = []        
        if format == 'pdf':
            for n, v in nvp:
                traffic_table_ramp.append([n,v])
        else:
            traffic_table_ramp = nvp
                 
        return traffic_table_ramp

    def getY156SAMTrafficBurstConfig(self, setup, format):
        burst_setup = setup['trafficShape']['burst']
        div_factor = 1000000
        nvp = \
        [
            ('% of The CBS/EBS', burst_setup['cbsp']/div_factor),
            ('Times of the MTU', burst_setup['mtum']),
            ('Second*(CIR/EIR)/8', burst_setup['cirp']),
            ('Burst Duty Cycle (%)', burst_setup['dutycycle']/div_factor),
            ('Number of Test Cycle', burst_setup['numofcycle'])
        ]       
        traffic_table_burst = []        
        if format == 'pdf':
            for n, v in nvp:
                traffic_table_burst.append([n,v])
        else:
            traffic_table_burst = nvp
                 
        return traffic_table_burst

    def getY156SAMServiceTableConfig(self, setup, format):
        cm = 'ON' if setup['bwpcos']['bwp'][0]['cm'] == 'ENABLE' else 'OFF'
        nvp = \
            [   ('Number Of Services', setup['evcmap']['nevc']),
                ('Color Mode', cm)
            ]
            
        traffic_table = []        
        if format == 'pdf':
            for n, v in nvp:
                traffic_table.append([n,v])
        else:
            traffic_table = nvp
                 
        return traffic_table


    def getY156SAMStreamFrameMacConfig(self, streamTable, format, sno):        
        try:
            setup = streamTable['macFrame']
        except:
            self.write_log('Y156sam Stream Mac setup data not found!', 'Error', sys.exc_info())
            return
        
        frame_type = get_param(setup,'macFrameType')
        
        if frame_type == 'IEEE802.3':
            eth_type = 'Length'
        else:
            eth_type = int_to_hex(setup['etherType'], 4, True)

        layerConfig = streamTable['layerConf']
        llcendis = 'Disable'
        snapendis = 'Disable'
        strllc =  get_param(layerConfig,'format802_2')
        if strllc == 'LLC' or strllc == 'SNAP':
            llcendis = 'Enable'

        if strllc == 'SNAP':
            snapendis = 'Enable'

        strip = get_param(layerConfig, 'layer234Type')
        if strip == 'IP' or strip == 'TCP' or strip == 'UDP':
            ip_on = 'Enable'
            tcp_on = 'Enable' if strip == 'TCP' else 'Disable'
            udp_on = 'Enable' if strip == 'UDP' else 'Disable'        
        else :
            ip_on = tcp_on = udp_on = 'Disable'
                    
        frametype = get_param_from_path(streamTable, 'frameSize', 'frameSizeType')
        framesize = get_param_from_path(streamTable, 'frameSize', 'constFrameLength')

        nvp = \
        [
            ('Frame Type', frame_type),
            ('Frame Size', framesize),
            ('Ethernet Type',eth_type),
            ('MAC Source',get_param(setup,'macSrc')),
            ('MAC Destination',get_param(setup,'macDest')),
            ('LLC', llcendis),
            ('SNAP',snapendis),
            ('VLAN',get_param(layerConfig,'enVlan', ENDI)),
            ('MPLS',get_param(layerConfig,'enMpls', ENDI)),
            ('IP',  ip_on),
            ('TCP', tcp_on),
            ('UDP', udp_on)
        ]
        stream_frame_mac_table = []
        if format == 'pdf':
            for n,v in nvp:
                stream_frame_mac_table.append([n,v])
        else:
            stream_frame_mac_table = nvp
        
        return stream_frame_mac_table

    def getY156SAMStreamVlanConfig(self, streamTable, format, sno):
        try:
            setup = streamTable['vlan']
        except:
            self.write_log('Y156sam Vlan setup data not found!', 'Error', sys.exc_info())
            return        
    
        num_vlans = get_param(streamTable, "nvlan")
        return self.getVlanTable(setup, num_vlans)

    def getY156SAMStreamIpConfig(self, streamTable, format, sno):
        try:
            setup = streamTable['ipHeader']
        except:
            self.write_log('Y156sam ipHeader setup data not found!', 'Error', sys.exc_info())
            return
        iptos = get_param(setup, 'iptos')
        
        nvp = \
            [   
                ('Source',get_param(setup,'ipSrc')),
                ('Destination',get_param(setup,'ipDest')),
                ('Default Gateway',get_param(setup,'ipGateway')),
                ('Subnet Mask',get_param(setup, 'subnetMask', '255.255.255.0')),
                ('IP Version',get_param(setup, 'versionAndLength')>>4),
                ('Protocol', get_param(setup, 'protocol')),
                ('Type of Service', iptos)
            ]
        tos = get_param(setup, 'tos')

        if iptos == 'RFC1349':
            precedence = tos>>5
            nvp.append(('Precedence', precedence))
            nvp.append(('Type of Service', hex((tos>>1)&0x0F)))
            nvp.append(('MBZ', tos & 0x01))
        else:
            nvp.append(('DSCP', int_to_hex(tos>>2, 2, True)))
            nvp.append(('Currently Unused', (tos & 0x03)))

        nvp.append(('Header Length',get_param(setup, 'versionAndLength')&0x0F))
        nvp.append(('Identifier', int_to_hex(setup['identifier'], 4, True)))

        fragFlagsAndOffset = get_param(setup, 'fragFlagsAndOffset')
        nvp.append(('Flag Don\'t Fragment', (fragFlagsAndOffset>>14)&0x01))
        nvp.append(('Flag More Fragment', (fragFlagsAndOffset>>13)&0x01))
        nvp.append(('Fragment Offset', fragFlagsAndOffset&0x1FFF))
        nvp.append(('Time To Live', get_param(setup, 'timeToLive')))

        # Stream IP Options
        if get_param(setup, 'enipopt') != 0:
            optlen = get_param(setup, 'optlen')
            nvp.append(('Length of IP Option', optlen))
            opt_data = setup['optdata'];
            num = 0
            for opt in opt_data:
                num = num + 1
                nvp.append(('Option Data %d' % num, int_to_hex(opt, 8, True)))
                if num >= optlen:
                    break
        else:
            nvp.append(('IP Option', 'Disable'))
    
        stream_ip_table = []
        if format == 'pdf':
            for n,v in nvp:
                stream_ip_table.append([n,v])
        else:
            stream_ip_table = nvp

        return stream_ip_table        

    def getY156SAMStreamMplsConfig(self, streamTable, format, sno):
        try:
            setup = streamTable['mplsCfg']
        except:
            self.write_log('Y156sam Mpls setup data not found!', 'Error', sys.exc_info())
            return

        num_mpls = get_param(streamTable, "nmpls")
            
        stream_mpls_setup = []
        if format == 'pdf':
            names = ['ID','Experimental','Bottom of Stack','Time to Live']
        else:
            names = ["ID","Experimental","Bottom of Stack","Time to Live"]
        stream_mpls_setup.append(names)
        
        
        for x in range(1,num_mpls+1):
            values = \
                [
                    hex(get_param(setup[x-1], 'hopLabel', 33024)),
                    get_param(setup[x-1], 'exp'),
                    get_param(setup[x-1], 'eofStack'),
                    get_param(setup[x-1], 'timeToLive')
                ]
            stream_mpls_setup.append(values)
        return stream_mpls_setup

    def getY156SAMStreamUdpConfig(self, streamTable, format, sno):
        try:
            setup = streamTable['udpHeader']
        except:
            self.write_log('Y156sam udpHeader setup data not found!', 'Error', sys.exc_info())
            return

        nvp = \
                [
                    ('Source Port',get_param(setup, 'SrcPort')),
                    ('Destination Port',get_param(setup, 'DestPort'))
                ]
        stream_udp_table = []
        if format == 'pdf':
            for n,v in nvp:
                stream_udp_table.append([n,v])
        else:
            stream_udp_table = nvp
            
        return stream_udp_table

    def getY156SAMStreamTcpConfig(self, streamTable, format, sno):
        try:
            setup = streamTable['tcpHeader']
        except:
            self.write_log('Y156sam tcpHeader setup data not found!', 'Error', sys.exc_info())
            return

        nvp = \
                [
                    ('Source Port', get_param(setup, 'SrcPort')),
                    ('Destination Port',get_param(setup, 'DestPort')),
                    ('Sequence Number',hex(get_param(setup, 'SeqNum'))),
                    ('ACK Number',hex(get_param(setup, 'AckNum'))),
                    ('Data Offset',altbin((get_param(setup, 'OffsetResFlags')>>12)&0x0F)),
                    ('Reserved 6 bits',altbin((get_param(setup, 'OffsetResFlags')>>6)&0x3F)),
                    ('Window Size',hex(get_param(setup, 'WinSize'))),
                    ('Urgent Pointer',hex(get_param(setup, 'UrgentPtr'))),
                    ('URG',(get_param(setup, 'OffsetResFlags')>>5)&0x01),
                    ('ACK',(get_param(setup, 'OffsetResFlags')>>4)&0x01),
                    ('PSH',(get_param(setup, 'OffsetResFlags')>>3)&0x01),
                    ('RST',(get_param(setup, 'OffsetResFlags')>>2)&0x01),
                    ('SYN',(get_param(setup, 'OffsetResFlags')>>1)&0x01),
                    ('FIN',(get_param(setup, 'OffsetResFlags')&0x01)),
                ]    
        stream_tcp_table = []
        if format == 'pdf':
            for n,v in nvp:
                stream_tcp_table.append([n,v])
        else:
            stream_tcp_table = nvp
        
        return stream_tcp_table

    def getY156SAMPayloadConfig(self, streamTable, format, sno):
        try:
            pattern = streamTable['pattern']
        except:
            self.write_log('Y156sam pattern setup data not found!', 'Error', sys.exc_info())
            return

        self.snts = True
        pattern_type = get_param(pattern, 'type')
        invert = 'ON' if get_param(pattern, 'invert') != 0 else 'OFF'
        nvp = \
        [ 
            ('Pattern Type',pattern_type)
        ]
        
        if pattern_type == 'USER':
            nvp.append( ('User Pattern Type','USER') )
            nvp.append( ('User Pattern',hex(get_param(pattern, 'userPattern')).rstrip('L')) )            
        elif pattern_type == 'USER1024':
            pat_data = pattern['userPattern1024']
            for i in range(1,33):
                nvp.append( ('Pattern Data %d'%i, hex(pat_data[i - 1]).rstrip('L')) )        
        elif pattern_type in ('ALL1','ALL0','ALT1'):
            pass
        else:
            nvp.append(('Invert', invert))            
            
        stream_payload_table = []
        if format == 'pdf':
            for n,v in nvp:
                stream_payload_table.append([n,v])
        else:
            stream_payload_table = nvp
            
        return stream_payload_table

    def getY156SAMStreamBWPCOSConfig(self, bwpcosno, format, sno):
        nvp = \
                [
                    ('BWP Number',bwpcosno[(sno-1)*2+0]+1),
                    ('SAC Number',bwpcosno[(sno-1)*2+1]+1)
                ]
        stream_bwp_cos_table = []
        if format == 'pdf':
            for n,v in nvp:
                stream_bwp_cos_table.append([n,v])
        else:
            stream_bwp_cos_table = nvp
            
        return stream_bwp_cos_table

    def getY156samResultStatus(self, status):
        y156sam_status = ['Pass', 'Fail', 'In Progress', 'N/A', 'Link Down', 'Complete', 'Cancel']
        try :
            resp = y156sam_status[status]
        except :
            resp = 'N/A'
        return resp

    def y156samSummary(self, fd, meas_data, format):
        try:
            events = meas_data['y156sam_event']
            test = events[0]['event']
        except:
            self.write_log('RFC2544 Latency result data not found!', 'Error', sys.exc_info())
            return

        table = []
        table.append(['Service Configuration Test', 'Service Performance Test'])
        if format == 'pdf':
            makeTable = self.createPdfTable
        else:
            makeTable = self.createCsvTable

        pageNo = 0
        total = get_param(events[pageNo]['event'], 'total')
        index = 0
        pos = 0

        configPass = "Not Started"
        perfomPass = "Not Started"
        while pos < total:
            try :
                if index == page_size: # go to begin of next page
                    pageNo += 1
                    index = 0

                seq = events[pageNo]['event'][str(index)]
                testMode = get_param(seq,'testMode')
                if  testMode < 5: # configuration test
                    configPass = self.getY156samResultStatus(get_param(seq,'configPassFail'))
                        
                if  testMode == 5: # performance test
                    perfomPass = self.getY156samResultStatus(get_param(seq,'performPassFail'))
                    
            except :
                self.write_log('', 'Error', sys.exc_info())
                break
            index += 1
            pos += 1

        row = \
        [
            configPass,
            perfomPass
        ]
        table.append(row)
            
        makeTable(fd, "Summary of Tests", table)
        self.write_log('process y156samSummary is done')

    def getY156samServiceConfPart1(self, fd, meas_data, format):
        try:
            events = meas_data['y156sam_event']
            test = events[0]['event']
        except:
            self.write_log('Y156Sam result data not found!')
            return

        table = []
        RTD_string = Paragraph('<para><font>RTD (&#181;s)</font></para>', styleSheet['Normal']).getPlainText()
        if format == 'pdf':
            makeTable = self.createPdfTable
            if meas_data['datatype'] == 'INFORATE':
                table = [['Test', 'Status', 'Information Rate (Mb/s)', '', '', 'Frame Loss', '', RTD_string, '', '']] 
            else :
                table = [['Test', 'Status', '   Line Rate (Mb/s)    ', '', '', 'Frame Loss', '', RTD_string, '', '']] 
            table.append([  '',                            
                            '',
                            ' Min ', ' Avg ', ' Max ', #Info Rate
                            'Rate (%)',
                            'Total',
                            ' Min ', ' Avg ', ' Max ', # RTD
                            ])

        else:
            table = []
            makeTable = self.createCsvTable
            if meas_data['datatype'] == 'INFORATE':
                table.append([  "Test", "Status", 
                                "Inform Rate (Mb/s) Min", "Inform Rate (Mb/s) Avg", "Inform Rate (Mb/s) Max",
                                "Frame Loss Rate (%)", "Frame Loss Total",
                                RTD_string + " Min", RTD_string + " Avg", RTD_string + " Max",])
            else :
                table.append([  "Test", "Status", 
                                "Line Rate (Mb/s) Min", "Line Rate (Mb/s) Avg", "Line Rate (Mb/s) Max",
                                "Frame Loss Rate (%)", "Frame Loss Total",
                                RTD_string + " Min", RTD_string + " Avg", RTD_string + " Max",])
        style = \
        [
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('BOX',(0,0),(-1,-1),1,colors.grey),
            ('SPAN',(2,0),(4,0)),
            ('SPAN',(5,0),(6,0)),
            ('SPAN',(7,0),(9,0)),
            ('SPAN',(0,0),(0,1)),
            ('SPAN',(1,0),(1,1)),
            ('ALIGN',(7,0),(9,0),'CENTER'),
            ('ALIGN',(2,0),(4,0),'CENTER'),
            ('ALIGN',(5,0),(6,0),'CENTER'),
            ('ALIGN',(2,2),(4,2),'CENTER'),
            ('BACKGROUND', (0,0), (-1, -1), colors.lavender),
        ]
        curcirseq = -1
        tempevc = -1
        curseq = -1
        durationRows = []
        serviceRows = []
        rowIndex = 2
        cir_duration_index = 0
        
        pageNo = 0
        total = get_param(events[pageNo]['event'], 'total')
        index = 0
        pos = 0

        while pos < total:
            if index == page_size:
                pageNo += 1
                index = 0

            seq = events[pageNo]['event'][str(index)]
            sequenceNum = get_param(seq,'sequenceNum')
            curevc = get_param(seq,'curevc')
            if curevc != tempevc:
                serviceRows.append(rowIndex)
                row = \
                    [
                    'Service #' + str(curevc + 1), '', '', '', '', '', '', '', '', ''
                    ]
                table.append(row)
                rowIndex += 1
                tempevc = curevc
                curcirseq = -1;

            testMode = get_param(seq,'testMode')
            CMode = get_param(seq,'CMode')
            status = self.getY156samResultStatus(get_param(seq['ir'][0],'passFail'))
            testStatus = self.getY156samResultStatus(get_param(seq,'status'))
            duration = get_param(seq,'duration')
            startTime = get_param(seq,'startTime')
            stopTime = get_param(seq,'stopTime')
            cirSequence = get_param(seq,'cirSequence')
            if testMode == 0 and curseq != sequenceNum and curcirseq != cirSequence:
                testMode = 'CIR'

                #CIR status have to use the last step data.
                row = \
                    [
                    testMode, testStatus,
                    'Duration:' + str(duration) + 'ms' + ', Started: ' + startTime + ',\nStopped: ' + stopTime,
                    '', '', '', '', '', '', '',
                    ]
                    
                if cirSequence == 0:
                    durationRows.append(rowIndex)
                    table.append(row)
                    cir_duration_index = rowIndex
                    rowIndex += 1
                else:
                    table.pop(cir_duration_index)
                    table.insert(cir_duration_index, row)

                step = 'Step ' + str(cirSequence + 1)
                row = \
                    [
                    step,
                    status,
                    get_param(seq['ir'][0],'IRMin'),
                    get_param(seq['ir'][0],'IRAvg'),
                    get_param(seq['ir'][0],'IRMax'),                       
                    get_param_float(seq['ir'][0],'FLRate', 0, 7),
                    get_param(seq['ir'][0],'FLTotal'),
                    get_param(seq['ir'][0],'RTDMin'),
                    get_param(seq['ir'][0],'RTDAvg'),
                    get_param(seq['ir'][0],'RTDMax'),
                    ]
                table.append(row)
                rowIndex += 1
                curcirseq = cirSequence

            if (testMode == 1 or testMode == 2 or testMode == 4) and curseq != sequenceNum:
                if testMode == 1:
                    testMode = 'CIR/EIR'
                elif testMode == 2:
                    testMode = 'TP'
                elif testMode == 4:
                    testMode = 'EBS'
                count = 1
                if count == 1:
                    durationRows.append(rowIndex)
                    row = \
                    [
                    testMode,
                    testStatus,
                    'Duration:' + str(duration) + 'ms' + ', Started: ' + startTime + ',\nStopped: ' + stopTime,
                    '', '', '', '', '', '', '',
                    ]
                    table.append(row)
                    rowIndex += 1
                if CMode != 1:
                    step = 'Total'
                    row = \
                        [
                        step,
                        status,
                        get_param(seq['ir'][0],'IRMin'),
                        get_param(seq['ir'][0],'IRAvg'),
                        get_param(seq['ir'][0],'IRMax'),                       
                        get_param_float(seq['ir'][0],'FLRate', 0, 7),
                        get_param(seq['ir'][0],'FLTotal', ICNA),
                        get_param(seq['ir'][0],'RTDMin'),
                        get_param(seq['ir'][0],'RTDAvg'),
                        get_param(seq['ir'][0],'RTDMax'),
                        ]
                    table.append(row)
                    rowIndex += 1
                else:
                    for c_ind in range(1, 4) :
                        if c_ind == 3 :
                            c_ind = 0   
                        rv = seq['ir'][c_ind]
                        status = self.getY156samResultStatus(get_param(rv,'passFail'))
                        if (c_ind > 0):
                            style.append(('BACKGROUND', (0,rowIndex), (9,rowIndex), [None, colors.limegreen, colors.yellow][c_ind]))
                        if status == 'Fail':
                            style.append(('BACKGROUND', (1, rowIndex), (1, rowIndex), colors.red))
                        row = \
                            [
                            ['Total', 'Green', 'Yellow'][c_ind],
                            status,
                            get_param(rv,'IRMin'),
                            get_param(rv,'IRAvg'),
                            get_param(rv,'IRMax'),                       
                            get_param_float(rv,'FLRate', 0, 7),
                            get_param(rv,'FLTotal', ICNA),
                            get_param(rv,'RTDMin'),
                            get_param(rv,'RTDAvg'),
                            get_param(rv,'RTDMax'),
                            ]
                        table.append(row)
                        rowIndex += 1
                        if c_ind == 0:
                            break
                        
                count += 1
                curseq = sequenceNum

            if testMode == 3 and curseq != sequenceNum:
                testMode = 'CBS'
                durationRows.append(rowIndex)
                row = \
                [
                testMode,
                testStatus,
                'Duration:' + str(duration) + 'ms' + ', Started: ' + startTime + ',\nStopped: ' + stopTime,
                '', '', '', '', '', '', '',
                ]
                table.append(row)
                rowIndex += 1

                step = ''
                row = \
                    [
                    step,
                    status,
                    get_param(seq['ir'][0],'IRMin'),
                    get_param(seq['ir'][0],'IRAvg'),
                    get_param(seq['ir'][0],'IRMax'),                       
                    get_param_float(seq['ir'][0],'FLRate', 0, 7),
                    get_param(seq['ir'][0],'FLTotal', ICNA),
                    get_param(seq['ir'][0],'RTDMin'),
                    get_param(seq['ir'][0],'RTDAvg'),
                    get_param(seq['ir'][0],'RTDMax'),
                    ]
                table.append(row)
                rowIndex += 1
                curseq = sequenceNum
            
            index += 1
            pos += 1

        if len(table) == 2:            
            no_data_row = ['']*table_width
            no_data_row[0] = 'No Data available'
            style.append( ('SPAN',(0,2),(table_width-1,2)) )
            table.append(no_data_row)

        for index in durationRows:
            try:
                style.append(('SPAN', (2, index), (9, index)))
            except: print 'Invalid row'
        for index in serviceRows:
            try:
                style.append(('SPAN', (0, index), (9, index)))
            except: print 'Invalid row'
        makeTable(fd, "Service Configuration Part 1", table, style)
        self.write_log('process getY156samServiceConfPart1` is done')
        
    def getY156samServiceConfPart2(self, fd, meas_data, format):
        try:
            events = meas_data['y156sam_event']
            test = events[0]['event']
        except:
            self.write_log('getY156samServiceConfPart2 result data not found!')
            return

        table = []
        FDV_string = Paragraph('<para><font>FDV (&#181;s)</font></para>', styleSheet['Normal']).getPlainText()
        if format == 'pdf':
            makeTable = self.createPdfTable
            
            table = [[ 'Test', 'Status', FDV_string, '', '', '    SES Total    ']] 
            table.append([  '',                            
                            '',
                            '     Min     ', '     Avg     ', '     Max     ',
                            '',
                            ])

        else:
            table = []
            makeTable = self.createCsvTable
            table.append([  "Test",
                            "Status",
                            FDV_string + " Min", FDV_string + " Avg", FDV_string + " Max",
                            "SES Total",
                            ])
            
        durationRows = []
        serviceRows = []
        rowIndex = 2
        style= \
        [
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('BOX',(0,0),(-1,-1),1,colors.grey),
            ('SPAN',(2,0),(4,0)),
            ('SPAN',(0,0),(0,1)),
            ('SPAN',(1,0),(1,1)),
            ('SPAN',(5,0),(5,1)),
            ('ALIGN',(2,0),(4,0),'CENTER'),
            ('BACKGROUND', (0,0), (-1, -1), colors.lavender),
        ]
        curseq = -1
        tempevc = -1
        curcirseq = -1
        count = 1
        
        pageNo = 0
        total = get_param(events[pageNo]['event'], 'total')
        index = 0
        pos = 0
        cir_duration_index = 0;
        while pos < total:
            if index == page_size:
                pageNo += 1
                index = 0
            seq = events[pageNo]['event'][str(index)]

            sequenceNum = get_param(seq,'sequenceNum')
            curevc = get_param(seq,'curevc')
            if curevc != tempevc:
                serviceRows.append(rowIndex)
                row = \
                    [
                    'Service #' + str(curevc + 1), '', '', '', '', '',
                    ]
                table.append(row)
                rowIndex += 1
                tempevc = curevc
                curcirseq = -1

            testMode = get_param(seq,'testMode')
            CMode = get_param(seq,'CMode')
            status = self.getY156samResultStatus(get_param(seq['ir'][0],'passFail'))
            testStatus = self.getY156samResultStatus(get_param(seq,'status'))
            duration = get_param(seq,'duration')
            startTime = get_param(seq,'startTime')
            stopTime = get_param(seq,'stopTime')
            cirSequence = get_param(seq,'cirSequence')
            if testMode == 0 and curseq != sequenceNum and curcirseq != cirSequence:
                testMode = 'CIR'

                #CIR status have to use the last step data.
                row = \
                    [
                    testMode, testStatus,
                    'Duration:' + str(duration) + 'ms' + ', Started: ' + startTime + ',\nStopped: ' + stopTime,
                    '', '', '',
                    ]
                    
                if cirSequence == 0:
                    durationRows.append(rowIndex)
                    table.append(row)
                    cir_duration_index = rowIndex
                    rowIndex += 1
                else:
                    table.pop(cir_duration_index)
                    table.insert(cir_duration_index, row)

                step = 'Step ' + str(cirSequence + 1)
                row = \
                    [
                    step,
                    status,
                    get_param(seq['ir'][0],'FDVMin'),
                    get_param(seq['ir'][0],'FDVAvg'),
                    get_param(seq['ir'][0],'FDVMax'),
                    get_param(seq['ir'][0],'SESTotal', ICNA),
                    ]
                table.append(row)
                rowIndex += 1
                curcirseq = cirSequence

            if (testMode == 1 or testMode == 2 or testMode == 4) and curseq != sequenceNum:
                if testMode == 1:
                    testMode = 'CIR/EIR'
                elif testMode == 2:
                    testMode = 'TP'
                elif testMode == 4:
                    testMode = 'EBS'

                count = 1
                if count == 1:
                    durationRows.append(rowIndex)
                    row = \
                    [
                    testMode,
                    testStatus,
                    'Duration:' + str(duration) + 'ms' + ', Started: ' + startTime + ',\nStopped: ' + stopTime,
                    '', '', '',
                    ]
                    table.append(row)
                    rowIndex += 1
                if CMode != 1:
                    step = 'Total'
                    row = \
                        [
                        step,
                        status,
                        get_param(seq['ir'][0],'FDVMin'),
                        get_param(seq['ir'][0],'FDVAvg'),
                        get_param(seq['ir'][0],'FDVMax'),
                        get_param(seq['ir'][0],'SESTotal', ICNA),
                        ]
                    table.append(row)
                    rowIndex += 1
                else:
                    for c_ind in range(1, 4) :
                        if c_ind == 3 :
                            c_ind = 0   
                        rv = seq['ir'][c_ind]
                        status = self.getY156samResultStatus(get_param(rv,'passFail'))
                        if (c_ind > 0):
                            style.append(('BACKGROUND', (0,rowIndex), (9,rowIndex), [None, colors.limegreen, colors.yellow][c_ind]))
                        if status == 'Fail':
                            style.append(('BACKGROUND', (1, rowIndex), (1, rowIndex), colors.red))
                        row = \
                            [
                            ['Total', 'Green', 'Yellow'][c_ind],
                            status,
                            get_param(rv,'FDVMin'),
                            get_param(rv,'FDVAvg'),
                            get_param(rv,'FDVMax'),
                            get_param(rv,'SESTotal', ICNA) if c_ind != 0 else NA,
                            ]
                        table.append(row)
                        rowIndex += 1
                        if c_ind == 0:
                            break
                count += 1
                curseq = sequenceNum

            if testMode == 3 and curseq != sequenceNum:
                testMode = 'CBS'
                durationRows.append(rowIndex)
                row = \
                [
                testMode,
                testStatus,
                'Duration:' + str(duration) + 'ms' + ', Started: ' + startTime + ',\nStopped: ' + stopTime,
                '', '', '',
                ]
                table.append(row)
                rowIndex += 1

                step = ''
                row = \
                    [
                    step,
                    status,
                    get_param(seq['ir'][0],'FDVMin'),
                    get_param(seq['ir'][0],'FDVAvg'),
                    get_param(seq['ir'][0],'FDVMax'),
                    get_param(seq['ir'][0],'SESTotal', ICNA),
                    ]
                table.append(row)
                rowIndex += 1
                curseq = sequenceNum
 
            index += 1
            pos += 1

        if len(table) == 2:            
            table_width = len(table[0])
            no_data_row = ['']*table_width
            no_data_row[0] = 'No Data available'
            style.append( ('SPAN',(0,2),(table_width-1,2)) )
            table.append(no_data_row)

        for index in durationRows:
            try:
                style.append(('SPAN', (2, index), (5, index)))
            except: print 'Invalid row, fail to SPAN'
        for index in serviceRows:
            try:
                style.append(('SPAN', (0, index), (5, index)))
            except: print 'Invalid row, fail to SPAN'
        makeTable(fd, "Service Configuration Part 2", table, style)
        self.write_log('process getY156samServiceConfPart2` is done')

    def getY156samServicePerfPart1(self, fd, meas_data, format):
        try:
            events = meas_data['y156sam_event']
            test = events[0]['event']
        except:
            self.write_log('getY156samServicePerfPart1 result data not found!')
            return

        table = []
        RTD_string = Paragraph('<para><font>RTD (&#181;s)</font></para>', styleSheet['Normal']).getPlainText()
        if format == 'pdf':
            makeTable = self.createPdfTable
            if meas_data['datatype'] == 'INFORATE':
                table = [['Test', 'Status', 'Information Rate (Mb/s)', '',  '', 'Frame Loss', '', RTD_string, '', '']]
            else :
                table = [['Test', 'Status', '   Line Rate (Mb/s)    ', '',  '', 'Frame Loss', '', RTD_string, '', '']]
            table.append([  '',                            
                            '',
                            '   Min   ', '   Avg   ', '   Max   ', #Info Rate
                            'Rate (%)',
                            'Total',
                            'Min', 'Avg', 'Max', # RTD
                            ])

        else:
            table = []
            makeTable = self.createCsvTable
            if meas_data['datatype'] == 'INFORATE':
                table.append([  "Test", "Status", 
                            "Inform Rate (Mb/s) Min", "Inform Rate (Mb/s) Avg", "Inform Rate (Mb/s) Max",
                            "Frame Loss Rate (%)", "Frame Loss Total",
                            RTD_string + " Minimum", RTD_string + " Average", RTD_string + " Maximum",])
            else :
                table.append([  "Test", "Status", 
                            "Inform Rate (Mb/s) Min", "Inform Rate (Mb/s) Avg", "Inform Rate (Mb/s) Max",
                            "Frame Loss Rate (%)", "Frame Loss Total",
                            RTD_string + " Minimum", RTD_string + " Average", RTD_string + " Maximum",])

        style = \
        [
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('BOX',(0,0),(-1,-1),1,colors.grey),
            ('SPAN',(2,0),(4,0)),
            ('SPAN',(5,0),(6,0)),
            ('SPAN',(7,0),(9,0)),
            ('SPAN',(0,2),(9,2)),
            ('SPAN',(0,0),(0,1)),
            ('SPAN',(1,0),(1,1)),
            ('ALIGN',(7,0),(9,0),'CENTER'),
            ('ALIGN',(2,0),(4,0),'CENTER'),
            ('ALIGN',(5,0),(6,0),'CENTER'),
            ('BACKGROUND', (0,0), (-1, -1), colors.lavender),
        ]

        tempevc = 100
        count = 1
        
        pageNo = 0
        total = get_param(events[pageNo]['event'], 'total')
        index = 0
        pos = 0
        while pos < total:
            if index == page_size:
                pageNo += 1
                index = 0
            seq = events[pageNo]['event'][str(index)]
            testMode = get_param(seq,'testMode')

            if testMode != 5:
                index += 1
                pos += 1
                continue
            
            duration = get_param(seq,'duration')
            startTime = get_param(seq,'startTime')
            stopTime = get_param(seq,'stopTime')
            row = \
                [
                 'Duration:' + str(duration) + 'ms' + ',Started: ' + startTime + ',Stopped: ' + stopTime,
                 '', '', '', '', '', '', '','',''
                 ]
            table.append(row)
            nevc = get_param(seq,'nevc')
            for count in range(1, nevc + 1):
                status = self.getY156samResultStatus(get_param(seq['ir'][count],'passFail'))
                row = \
                    [
                    'Service #' + str(count),
                    status,
                    get_param(seq['ir'][count],'IRMin') if status != 'N/A' else 'N/A',
                    get_param(seq['ir'][count],'IRAvg') if status != 'N/A' else 'N/A',
                    get_param(seq['ir'][count],'IRMax') if status != 'N/A' else 'N/A',
                    get_param_float(seq['ir'][count],'FLRate',0 , 7) if status != 'N/A' else 'N/A',
                    get_param(seq['ir'][count],'FLTotal', ICNA) if status != 'N/A' else 'N/A',
                    get_param(seq['ir'][count],'RTDMin') if status != 'N/A' else 'N/A',
                    get_param(seq['ir'][count],'RTDAvg') if status != 'N/A' else 'N/A',
                    get_param(seq['ir'][count],'RTDMax') if status != 'N/A' else 'N/A',
                    ]
                table.append(row)
            break

        if len(table) == 2:            
            table_width = len(table[0])
            no_data_row = ['']*table_width
            no_data_row[0] = 'No Data available'
            style.append( ('SPAN',(0,2),(table_width-1,2)) )
            table.append(no_data_row)

        makeTable(fd, "Service Performance Part 1", table, style)
        self.write_log('process getY156samServicePerfPart`` is done')

    def getY156samServicePerfPart2(self, fd, meas_data, format):
        try:
            events = meas_data['y156sam_event']
            test = events[0]['event']
        except:
            self.write_log('getY156samServicePerfPart1 result data not found!')
            return

        table = []
        FDV_string = Paragraph('<para><font>FDV (&#181;s)</font></para>', styleSheet['Normal']).getPlainText()
        if format == 'pdf':
            makeTable = self.createPdfTable
            
            table = [[ 'Test', 'Status', FDV_string, '', '', 'SES Total', 'Availability', '', '', '']] 
            table.append([  '',                            
                            '',
                            'Min', 'Avg', 'Max',
                            '',
                            'Avail', 'Unav', 'Av(%)', 'Unav(%)'
                            ])

        else:
            table = []
            makeTable = self.createCsvTable
            table.append([  "Test",
                            "Status",
                            FDV_string + " Minimum", FDV_string + " Average", FDV_string + " Maximum",
                            "SES Total",
                            "Avail", "Unavail", "Avail (%)", "Unavail (%)",
                            ])
        style= \
        [
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('BOX',(0,0),(-1,-1),1,colors.grey),
            ('SPAN',(2,0),(4,0)),
            ('SPAN',(6,0),(9,0)),
            ('SPAN',(0,0),(0,1)),
            ('SPAN',(1,0),(1,1)),
            ('SPAN',(5,0),(5,1)),
            ('SPAN',(0,2),(9,2)),
            ('ALIGN',(2,0),(4,0),'CENTER'),
            ('ALIGN',(6,0),(9,0),'CENTER'),
            ('BACKGROUND', (0,0), (-1, -1), colors.lavender),
        ]

        tempevc = 100
        count = 1
        pageNo = 0
        total = get_param(events[pageNo]['event'], 'total')
        index = 0
        pos = 0
        while pos < total:
            if index == page_size:
                pageNo += 1
                index = 0
            seq = events[pageNo]['event'][str(index)]

            testMode = get_param(seq,'testMode')
            testStatus = self.getY156samResultStatus(get_param(seq,'overallPassFail'))

            if testMode != 5:                
                index += 1
                pos += 1
                continue
            
            duration = get_param(seq,'duration')
            startTime = get_param(seq,'startTime')
            stopTime = get_param(seq,'stopTime')
            row = \
                [
                 'Duration:' + str(duration) + 'ms' + ',Started: ' + startTime + ',Stopped: ' + stopTime,
                 '', '', '', '', '', '', '', '', ''
                ]
            table.append(row)

            nevc = get_param(seq,'nevc')
            for count in range(1, nevc + 1):
                status = self.getY156samResultStatus(get_param(seq['ir'][count],'passFail'))
                row = \
                    [
                    'Service #' + str(count),
                    status,
                    get_param(seq['ir'][count],'FDVMin') if status != 'N/A' else 'N/A',
                    get_param(seq['ir'][count],'FDVAvg') if status != 'N/A' else 'N/A',
                    get_param(seq['ir'][count],'FDVMax') if status != 'N/A' else 'N/A',
                    get_param(seq['ir'][count],'SESTotal', ICNA) if status != 'N/A' else 'N/A',
                    get_param(seq['ir'][count],'availableSec', ICNA) if status != 'N/A' else 'N/A',
                    get_param(seq['ir'][count],'unavailableSec', ICNA) if status != 'N/A' else 'N/A',
                    get_param(seq['ir'][count],'PEA') if status != 'N/A' else 'N/A',
                    get_param(seq['ir'][count],'PEU') if status != 'N/A' else 'N/A',
                    ]
                table.append(row)
            break
        
        if len(table) == 2:            
            table_width = len(table[0])
            no_data_row = ['']*table_width
            no_data_row[0] = 'No Data available'
            style.append( ('SPAN',(0,2),(table_width-1,2)) )
            table.append(no_data_row)

        makeTable(fd, "Service Performance Part 2", table, style)
        self.write_log('process getY156samServicePerfPart2`` is done')


    def rfc2544SetupFC(self, fd, config, params, format):
        try:
            setup = config['config']['ether']['stFCR2544Config']
        except:
            self.write_log('FC RFC2544 setup data not found!', 'Error')
            return

        streamTable = setup['streamTable'][0]

        # Set the Table Creation function
        if format == 'pdf':
            makeTable = self.createPdfTable
        elif format == 'csv':
            makeTable = self.createCsvTable
        else:
            self.write_log("Format Not Specified, Exiting")
            return  

        # Make Setup Table
        setup_table = self.getRFC2544SetupConfigFC(setup, params, format)
        makeTable(fd, 'RFC2544 Test Setup',setup_table)           
       
        # Make Frame Table
        frame_table = self.getRFC2544FrameConfigFC(setup, format)
        makeTable(fd, 'Frame Setup',frame_table)

        # Make Throughtput Table
        if setup['throughput']:
            thrput_table = self.getRFC2544ThruputConfigFC(setup, params, format)
            makeTable(fd, 'Throughput Setup',thrput_table)     

        # Make Latency Table
        if setup['latency']:# and params['tputLatency'] == True:
            latency_table = self.getRFC2544LatencyConfigFC(setup, params, format)
            makeTable(fd, 'Latency Setup',latency_table)
            
        # Make Frame Loss Table
        if setup['frameLoss']:# and params['flTable'] == True:  
            frame_loss_table = self.getRFC2544FrameLossConfigFC(setup, format)
            makeTable(fd, 'Frame Loss Setup',frame_loss_table) 

        # Make Back to Back Setup Table
        if setup['backToBack']: #and params['bbTable'] == True:
            back2back_table = self.getRFC2544BacktoBackConfigFC(setup, format)
            makeTable(fd, 'Back to Back Setup',back2back_table)

        # Stream Setup Booleans
        self.throughputStreamFrameSetupFC(fd, setup, format, False)               
        self.throughputStreamFrameHeaderFC(fd, setup, format, False)
        self.throughputStreamPayloadFC(fd, setup, format, False)
        #self.log.debug("END RFC2544 Setup %s"%format)

    def getRFC2544SetupConfigFC(self, setup, params, format):
        latencyType = get_param_from_path(setup, 'sequence', 'latencyType')
        if latencyType == 1: latencyType = 'Quick'
        else: latencyType = 'Standard'
        
        rfctype = get_param(setup, 'standardMode')
        if rfctype == 0: rfctype = 'RFC2544'
        else: rfctype = NA
        
        nvp = \
        [
            ('Test Type', rfctype),
            ('Throughput', setup['sequence']['sequenceOn'][0] == 1),
            ('Latency', setup['sequence']['sequenceOn'][1] == 1),
            ('Latency Mode', latencyType),
            ('Frame Loss', setup['sequence']['sequenceOn'][2] == 1),
            ('Back to Back', setup['sequence']['sequenceOn'][3] == 1)
        ]                             
        setup_table = []        
        if format == 'pdf':        
            for n, v in nvp:
                setup_table.append([n,v])
        else:
            setup_table = nvp
                 
        return setup_table
        
    def getRFC2544FrameConfigFC(self, config, format):
        setup = config['frame']

        frame_table = []
        if format == 'pdf':
            lat_string = Paragraph('<para><font>Latency (&#181;s)</font></para>', styleSheet['Normal']).getPlainText()
            frame_table.append(['Length' , 'Throughput %' , lat_string])
        else:
            frame_table.append(["Length","Throughput %","Latency (us)"])

        #totalFrame = get_param(setup, 'totalFrame')
        totalFrame = 10
        i = 0
        while i < totalFrame:
            if setup['activeFrame'][i] == 1:
                if setup['thresholdOn']:
                    row =  \
                    [
                        setup['frameSize'][i],
                        setup['throughput'][i],
                        setup['latency'][i]
                    ]
                else:
                    row =  \
                    [
                        setup['frameSize'][i],
                        NA,
                        NA
                    ]                    
                frame_table.append(row)
            i += 1
            
        return frame_table
        
    def getRFC2544ThruputConfigFC(self, setup, params, format):
        try:
            setup = setup['throughput']
        except:
            self.write_log('FC RFC2544 ThruputConfig data not found!')
            return
        
        thru_type = get_param(setup, 'durationType')
        if thru_type == 0: thru_type = 'TIME'
        else: thru_type = 'FRAMES'
        if thru_type == 'TIME':
            time_or_frames = 'Time (sec)'
            duration = get_param(setup, 'durationSec')
        elif thru_type == 'FRAMES':
            time_or_frames = 'Frames'                    
            duration = get_param(setup, 'durationFrame')

        nvp = \
        [
            ('Duration Type', thru_type),
            (time_or_frames,duration),
            ('Start Rate (%)', get_param(setup, 'startRate')),
            ('Resolution (%)', get_param(setup, 'stepRate'))
        ]
        
        thrput_table = []
        if format == 'pdf':
            for n, v in nvp:
                thrput_table.append([n,v])
        else:
            thrput_table = nvp
    
        return thrput_table            

    def getRFC2544LatencyConfigFC(self, setup, params, format):
        try:
            setup = setup['latency']
        except:
            self.write_log('FC RFC2544 LatencyConfig data not found!', 'Error')
            return
        nvp = \
        [
            #('Test Type', get_param_from_path(setup, 'latency', 'latencyMode')),
            ('Duration (sec)', get_param(setup, 'durationSec')),
            ('Warm-up (sec)', get_param(setup, 'warmupSec')),
            ('Repetitions', get_param(setup, 'repetition')),
        ]

        rate_type = get_param(setup, 'rateType')
        if rate_type == 0: rate_type = 'THROUGHPUT'
        else: rate_type = 'CUSTOM'
        
        nvp.append( ('Rate Type', rate_type) )
        if rate_type == 'CUSTOM':                      
            nvp.append( ('Custom Rate', get_param(setup, 'customRate')) )
        
        latency_table = []
        if format == 'pdf':            
            for n, v in nvp:
                latency_table.append([n,v])
        else:
            latency_table = nvp
        
        return latency_table

    def getRFC2544FrameLossConfigFC(self, config, format):
        try:
            setup = config['frameLoss']
        except:
            self.write_log('RFC2544 FrameLossConfig data not found!', 'Error')
            return

        frame_loss_type = get_param(setup, 'durationType')
        if frame_loss_type == 0: frame_loss_type = 'TIME'
        else: frame_loss_type = 'FRAMES'
        if frame_loss_type == 'TIME':
            time_or_frames = 'Duration Time (sec)'
            duration = get_param(setup, 'durationSec')
        elif frame_loss_type == 'FRAMES':
            time_or_frames = 'Duration Frames'                    
            duration = get_param(setup, 'durationFrame')
    
        nvp = \
        [
            ('Test Type', frame_loss_type),
            (time_or_frames ,duration),
            ('Start Rate (%)', get_param(setup, 'startRate'))
        ]
        
        nvp.append( ('Rate Step Size (%)', get_param(setup, 'stepRate')) )
        
        frame_loss_table = []
        if format == 'pdf':
            for n, v in nvp:
                frame_loss_table.append([n,v])
        else:
            frame_loss_table = nvp
        
        return frame_loss_table

    def getRFC2544BacktoBackConfigFC(self, setup, format):
        try:
            setup = setup['backToBack']
        except:
            self.write_log('RFC2544 BacktoBackConfig data not found!', 'Error')
            return

        nvp = \
        [
            ('Time Duration (sec)', get_param(setup, 'durationSec')),
            ('Max Duration (sec)', get_param(setup, 'maxDurationSec')),
            ('Repetitions', get_param(setup, 'repetition')),
            ('Frames Resolution', get_param(setup, 'resolutionFrame')),
        ]   
                                  
        back2back_table = []
        
        if format == 'pdf':        
            for n, v in nvp:
                back2back_table.append([n,v])
        else:
            back2back_table = nvp
            
        return back2back_table  

    def b2bSetupFC(self, fd, config, params, format):
        try:
            setup = config['config']['ether']['stFCB2BConfig']
        except:
            self.write_log('FC B2B setup data not found!', 'Error')
            return
        
        streamTable = setup['streamTable'][0]

        # Make Frame Table
        self.getB2BFrameConfigFC(fd, setup, format)

        # Stream Setup Booleans
        self.throughputStreamFrameHeaderFC(fd, setup, format, False)
        self.throughputStreamPayloadFC(fd, setup, format, False)
        #self.log.debug("END B2B Setup %s"%format)
        
    def getB2BFrameConfigFC(self, fd, config, format):
        setup = config['FramesConfig']
        
        #NUM_OF_E_FC_B2BFRAMETYPE = 9
        totalFrame = 9;

        frame_table = []
        frame_table.append(["Length","Throughput %", "Time Out"])

        i = 0
        while i < totalFrame:
            if setup[i]['bEnabled'] == 1:
                row =  \
                [
                    setup[i]['ulFrameLength'],
                    setup[i]['ulBandwidth']/1000000,
                    config['b2bTestTime']
                ]
                     
                frame_table.append(row)
            i += 1

        if format == 'pdf':
            makeTable = self.createPdfTable
        elif format == 'csv':
            makeTable = self.createCsvTable
            
        makeTable(fd, 'Frame Setup',frame_table)

    def b2bResultTableFC(self, fd, meas_data, format):
        try:
            results = meas_data['fc_b2b_event']['result']
        except:
            self.write_log('FC B2B result data not found!', 'Error')
            return
        
        table = [['Frame Size\n(bytes)', 'Throughput %', 'Number of Buffer Credit Required']]

        if format == 'pdf':
            makeTable = self.createPdfTable
        else:
            makeTable = self.createCsvTable
        
        status = [NA, 'Pass']

        quick_Latency = False
        count = get_param(results, 'count')
        index = 0
        while index < count:
            rowdata = results[str(index)]

            row = []
            row.extend([get_param(rowdata, 'framelen'), 
                        #get_param(rowdata, 'cbw', NNA),
                        int(rowdata['cbw']),
                        get_param(rowdata, 'ncredit')
                        ])

            table.append(row)
            index += 1

        style=[ \
            ('GRID',(0,0),(-1,-1),0.5, colors.grey),
            ('BOX',(0,0),(-1,-1),1, colors.grey),
            ('ALIGN',(0,0),(2,0),'CENTER'),
            ('VALIGN',(0,0),(0,0),'MIDDLE'),
            ('BACKGROUND', (0,0), (-1, -1), colors.lavender),
            ]

        if len(table) == 1:            
            no_data_row = ['No Data Available', '', '']
            style.append(('SPAN', (0, 1), (2, 1)))
            table.append(no_data_row)

        makeTable(fd, "B2B Result", table, style)
        

    def rfc2544Setup(self, fd, config, params, format):
        try:
            setup = config['config']['ether']['stR2544Config']
        except:
            self.write_log('RFC2544 setup data not found!', 'Error', sys.exc_info())
            return
        
        streamTable = setup['streamTable'][0]

        # Set the Table Creation function
        if format == 'pdf':
            makeTable = self.createPdfTable
        elif format == 'csv':
            makeTable = self.createCsvTable
                        
        # Make Setup Table                               
        setup_table = self.getRFC2544SetupConfig(setup, params, format)
        makeTable(fd, 'RFC2544 Test Setup',setup_table)           
       
        # Make Frame Table
        frame_table = self.getRFC2544FrameConfig(setup, format)
        makeTable(fd, 'Frame Setup',frame_table)

        # Make Throughtput Table
        if setup['throughput']:
            thrput_table = self.getRFC2544ThruputConfig(setup, params, format)
            makeTable(fd, 'Throughput Setup',thrput_table)     

        # Make Latency Table
        if setup['latency']:# and params['tputLatency'] == True:      
            latency_table = self.getRFC2544LatencyConfig(setup, params, format)
            makeTable(fd, 'Latency Setup',latency_table)
            
        # Make Frame Loss Table
        if setup['frameLoss']:# and params['flTable'] == True:      
            frame_loss_table = self.getRFC2544FrameLossConfig(setup, format)
            makeTable(fd, 'Frame Loss Setup',frame_loss_table) 

        # Make Back to Back Setup Table
        if setup['backToBack']: #and params['bbTable'] == True:
            back2back_table = self.getRFC2544BacktoBackConfig(setup, format)
            makeTable(fd, 'Back to Back Setup',back2back_table)

        # Get Stream Setup Booleans
        try:
            layerConf = streamTable['layerConf']
        except:
            layerConf = {}
        vlan_on = get_param(layerConf, 'enVlan', NNA)
        mpls_on = get_param(layerConf, 'enMpls', NNA)
        strip = get_param(layerConf, 'layer234Type')
        tcp_on = get_param(setup, 'enTcp', NNA)
        udp_on = get_param(setup, 'enUdp', NNA)
        ip_on = get_param(setup, 'enIp', NNA)
        
        # Stream Frame Setup
        stream_general = self.getRFC2544StreamGeneralConfig(streamTable, format)
        makeTable(fd, 'General Stream Setup',stream_general)

        stream_frame_table = self.getRFC2544StreamFrameConfig(streamTable, format)
        makeTable(fd, 'Mac Setup',stream_frame_table)
        
        # Stream VLAN Setup
        if vlan_on != 0:
            stream_vlan_table = self.getRFC2544StreamVlanConfig(streamTable,format)
            makeTable(fd, 'Stream VLAN Setup',stream_vlan_table)
        
        # Stream MPLS Setup
        if mpls_on != 0:
            stream_mpls_table = self.getRFC2544StreamMplsConfig(streamTable, format)
            makeTable(fd, 'Stream MPLS Setup',stream_mpls_table)
            
        # Stream IP Setup
        if strip == 'IP' or strip == 'TCP' or strip == 'UDP':
            stream_ip_table = self.getRFC2544StreamIpConfig(streamTable, format)
            makeTable(fd, 'Stream IP Setup',stream_ip_table)
            
        # UDP Setup
        if strip == 'UDP':
            stream_udp_table = self.getRFC2544StreamUdpConfig(streamTable, format)
            makeTable(fd, 'Stream UDP Setup',stream_udp_table)
            
        # TCP Setup
        if strip == 'TCP':
            stream_tcp_table = self.getRFC2544StreamTcpConfig(streamTable, format)
            makeTable(fd, 'Stream TCP Setup',stream_tcp_table)
            
        # Payload Setup
        stream_payload_table = self.getRFC2544PayloadConfig(streamTable, format)   
        makeTable(fd, 'Stream Payload Setup',stream_payload_table)

    def getRFC2544SetupConfig(self, setup, params, format):
        #print 'getRFC2544SetupConfig(%s, %s)'%(setup, format)
        latencyType = get_param_from_path(setup, 'sequence', 'latencyType')
        if latencyType == 0: latencyType = 'Standard'
        else: latencyType = 'Quick'
        
        rxportID = get_param(setup, 'rxPortID')
        if get_param(setup, 'txPortID') == NA: txportID = get_param(setup, 'rxPortID')
        else: txportID = get_param(setup, 'txPortID')
        txportID = 'P%d' % int(txportID)
        rxportID = 'P%d' % int(rxportID)

        if setup['standardMode'] == 0:
            testmode = 'RFC2544' 
        else:
            testmode = 'NE Test' 
        
        sequenceOn = setup['sequence']['sequenceOn']
        #print latencyType, rxportID, txportID, sequenceOn
        nvp = \
        [
            ('Tx Port', txportID),
            ('Rx Port', rxportID),
            ('Test Type', testmode),
            #('Run Continuously', get_param_from_path(setup, 'sequence', 'continuousOn', ENDI)),
            #('Trial Description', bool(get_param_from_path(setup, 'sequence', 'trialDescOn'))),
            #('DUT Type ID', get_param_from_path(setup, 'sequence', 'dutType')),
            ('Throughput', ['Disable', 'Enable'][sequenceOn[0]]),
            ('Frame Size Thresholds', get_param_from_path(setup, 'frame', 'thresholdOn', ENDI)),
            ('Latency', ['Disable', 'Enable'][sequenceOn[1]]),
            ('Latency Mode', latencyType),
            ('Frame Loss', ['Disable', 'Enable'][sequenceOn[2]]),
            ('Back to Back', ['Disable', 'Enable'][sequenceOn[3]])
        ]                       
        #print nvp
                      
        setup_table = []        
        if format == 'pdf':        
            for n, v in nvp:
                setup_table.append([n,v])
        else:
            setup_table = nvp
                 
        return setup_table   

    def getRFC2544FrameConfig(self, config, format):
        setup = config['frame']
        #print 'getRFC2544FrameConfig', setup
        
        totalFrame = get_param(setup, 'totalFrame')
        
        frame_table = []
        if format == 'pdf':
            lat_string = Paragraph('<para><font>Latency (&#181;s)</font></para>', styleSheet['Normal']).getPlainText()
            frame_table.append(['Length' , 'Throughput %' , lat_string])
        else:
            frame_table.append(["Length","Throughput %","Latency (us)"])
        
        i = 0
        while i < 10:                   
            if setup['activeFrame'][i] == 0:
                i += 1
                continue
            if setup['thresholdOn']:
                row =  \
                [
                    setup['frameSize'][i],
                    setup['throughput'][i],
                    setup['latency'][i]
                ]
            else:
                row =  \
                [
                    setup['frameSize'][i],
                    NA,
                    NA
                ]                    
            frame_table.append(row)
            i += 1
            
        return frame_table

    def getRFC2544ThruputConfig(self, setup, params, format):
        try:
            setup = setup['throughput']
        except:
            self.write_log('RFC2544 ThruputConfig data not found!', 'Error', sys.exc_info())
            return
        #print 'getRFC25444ThroughputConfig ', setup

        thru_type = get_param(setup, 'durationType')
        if thru_type == 0: thru_type = 'TIME'
        else: thru_type = 'FRAMES'
        if thru_type == 'TIME':
            time_or_frames = 'Time (sec)'
            duration = get_param(setup, 'durationSec')
        elif thru_type == 'FRAMES':
            time_or_frames = 'Frames'                    
            duration = get_param(setup, 'durationFrame')
               
        nvp = \
        [
            ('Duration Type', thru_type),
            (time_or_frames,duration),
            ('Start Rate (%)', get_param(setup, 'startRate'))            
        ]
        
        #print 'getRFC25444ThroughputConfig 222', nvp
        test_type = get_param(params, 'testmode')
        if test_type == 'RFC2544':
            nvp.append( ('Resolution (%)', get_param(setup, 'stepRate')))#'durationFrame'
        else:
            nvp.append( ('Stop Rate (%)', get_param(setup, 'stopRate')) )
            nvp.append( ('Rate Step Size (%)', get_param(setup, 'stepRate')) )
        
        thrput_table = []
        if format == 'pdf':
            for n, v in nvp:
                thrput_table.append([n,v])
        else:
            thrput_table = nvp
    
        return thrput_table            

    def getRFC2544LatencyConfig(self, setup, params, format):
        try:
            setup = setup['latency']
        except:
            self.write_log('RFC2544 LatencyConfig data not found!', 'Error', sys.exc_info())
            return
        #print 'getRFC25444LatencyConfig ', setup

        nvp = \
        [
            #('Test Type', get_param_from_path(setup, 'latency', 'latencyMode')),
            ('Duration (sec)', get_param(setup, 'durationSec')),
            ('Warm-up (sec)', get_param(setup, 'warmupSec')),
            ('Repetitions', get_param(setup, 'repetition')),
        ]
        
        #print 'getRFC25444LatencyConfig ', nvp
        
        test_type = get_param(params, 'testmode')
        if test_type == 'RFC2544':
            rate_type = get_param(setup, 'rateType')
            if rate_type == 0: rate_type = 'THROUGHPUT'
            else: rate_type = 'CUSTOM'
            
            nvp.append( ('Rate Type', rate_type) )
            if rate_type == 'CUSTOM':                      
                nvp.append( ('Custom Rate', get_param(setup, 'customRate')) )
            else:
                nvp.append( ('Start Rate (%)', get_param(setup, 'startRate')) )
                nvp.append( ('Stop Rate (%)', get_param(setup, 'stopRate')) )
                nvp.append( ('Rate Step Size (%)', get_param(setup, 'stepRate')) )
        
        latency_table = []
        if format == 'pdf':            
            for n, v in nvp:
                latency_table.append([n,v])
        else:
            latency_table = nvp
        
        return latency_table

    def getRFC2544FrameLossConfig(self, setup, format):
        try:
            setup = setup['frameLoss']
        except:
            self.write_log('RFC2544 FrameLossConfig data not found!', 'Error', sys.exc_info())
            return
        #print 'getRFC25444FrameLossConfig ', setup

        frame_loss_type = get_param(setup, 'durationType')
        if frame_loss_type == 0: frame_loss_type = 'TIME'
        else: frame_loss_type = 'FRAMES'
        if frame_loss_type == 'TIME':
            time_or_frames = 'Time (sec)'
            duration = get_param(setup, 'durationSec')
        elif frame_loss_type == 'FRAMES':
            time_or_frames = 'Frames'                    
            duration = get_param(setup, 'durationFrame')
    
        nvp = \
        [
            ('Test Type', frame_loss_type),
            (time_or_frames ,duration),
            ('Start Rate (%)', get_param(setup, 'startRate'))
        ]
        
        #print 'getRFC25444FrameLossConfig ', nvp
        test_type = get_param(setup,'SET-RFC2544-TYPE','rtype')
        if test_type == 'RFC2544':
            nvp.append( ('Rate Step Size (%)', get_param(setup, 'stepRate')) )
        else:
            #nvp.append( ('Stop Rate (%)', get_param(setup, 'stopRate')) )
            nvp.append( ('Rate Step Size (%)', get_param(setup, 'stepRate')) )
        
        frame_loss_table = []
        if format == 'pdf':
            for n, v in nvp:
                frame_loss_table.append([n,v])
        else:
            frame_loss_table = nvp
        
        return frame_loss_table

    def getRFC2544BacktoBackConfig(self, setup, format):
        try:
            setup = setup['backToBack']
        except:
            self.write_log('RFC2544 BacktoBackConfig data not found!', 'Error', sys.exc_info())
            return
        #print 'getRFC2544BacktoBackConfig ', setup
        
        b2b_type = get_param(setup, 'resolutionType')
        if b2b_type == 0:
            b2b_type = 'FRAMES'
            percent_or_frames = 'Frames'
            duration = get_param(setup, 'resolutionFrame')
        elif b2b_type == 1:
            b2b_type == 'PERCENTAGE'
            percent_or_frames = 'Percentage (%)'
            duration = get_param(setup, 'resolutionPercent')
    
        nvp = \
        [
            ('Time Duration (sec)', get_param(setup, 'durationSec')),
            ('Max Duration (sec)', get_param(setup, 'maxDurationSec')),
            ('Repetitions', get_param(setup, 'repetition')),
            #('Resolution Type', get_param(setup, 'resolutionType')),
            #(percent_or_frames, duration)
        ]   
                                  
        #print 'getRFC2544BacktoBackConfig ', nvp
        back2back_table = []
        
        if format == 'pdf':        
            for n, v in nvp:
                back2back_table.append([n,v])
        else:
            back2back_table = nvp
            
        return back2back_table  

    def getRFC2544StreamGeneralConfig(self, stream_table, format):
       
        table = []
        names_inserted = False
            
        layerConf = stream_table['layerConf']
        ipHeader = stream_table['ipHeader']
        structure = 'MAC'            

        layer_type = get_param(layerConf, 'layer234Type', False)
        if layer_type == 'IP':
            structure += ' IP '
        elif layer_type == 'TCP':
            structure += ' IP TCP'
        elif layer_type == 'UDP':
            structure += ' IP UDP '

        if get_param(layerConf, 'enMacInMac', False):
            structure += ' MACinMAC ' 
        if get_param(layerConf, 'enVlan', False):
            structure += ' VLAN ' 
        if get_param(layerConf, 'enMpls', False):
            structure += ' MPLS '
        
        structure = structure.strip(' ')
        frametype = get_param_from_path(stream_table, 'frameSize', 'frameSizeType')
        framesize = get_param_from_path(stream_table, 'frameSize', 'constFrameLength')
        nvp = \
            [
                ('Stream No.', 1),
                ('Structure', structure),
                #('Frame Type', frametype),
                #('Frame Size', framesize)
            ]            
        names = []
        values = []
        for n,v in nvp:
            if format == 'pdf':
                makeTable = self.createPdfTable
                names.append(n)
            else:
                makeTable = self.createCsvTable
                names.append(CSV_NAME(n))
            values.append(v)
           
        if not names_inserted:
            table.append(names)
            names_inserted = True
        
        table.append(values)

        return table

    def getRFC2544StreamFrameConfig(self, streamTable, format):
        setup = streamTable['macFrame']

        setup2 = streamTable['layerConf']
        llcendis = 'Disable'
        snapendis = 'Disable'
        strllc =  get_param(setup2,'format802_2')
        if strllc == 'LLC' or strllc == 'SNAP':
            llcendis = 'Enable'

        if strllc == 'SNAP':
            snapendis = 'Enable'

        frame_type = get_param(setup,'macFrameType')
        if frame_type == 'IEEE802.3':
            eth_type = 'Length'
        else:
            eth_type = int_to_hex(setup['etherType'], 4, True)

        nvp = \
        [
            ('Frame Type', get_param(setup, 'macFrameType')),
            ('Ethernet Type', eth_type),
            ('MAC Source', get_param(setup, 'macSrc')),
            ('MAC Destination', get_param(setup, 'macDest')),
            ('LLC', llcendis),
            ('SNAP', snapendis),
            #('VLAN', get_param(setup,'SET-RFC2544-CONFIG','envlan')),
            #('MPLS', get_param(setup,'SET-RFC2544-CONFIG','enmpls')),
            #('TCP', get_param(setup,'SET-RFC2544-CONFIG','entcp')),
            #('UDP', get_param(setup,'SET-RFC2544-CONFIG','enudp')),
            #('IP', get_param(setup,'SET-RFC2544-CONFIG','enip'))
        ]
        stream_frame_table = []
        if format == 'pdf':
            for n,v in nvp:
                stream_frame_table.append([n,v])
        else:
            stream_frame_table = nvp
        
        return stream_frame_table

    def getRFC2544StreamVlanConfig(self, streamTable, format):
        try:
            setup = streamTable['vlan']
        except:
            self.write_log('RFC2544 StreamVlanConfig data not found!', 'Error', sys.exc_info())
            return
        
        num_vlans = get_param(streamTable, "nvlan")
        return self.getVlanTable(setup, num_vlans)

    def getRFC2544StreamIpConfig(self, streamTable, format):
        try:
            setup = streamTable['ipHeader']
        except:
            self.write_log('RFC2544 ipHeader setup data not found!', 'Error', sys.exc_info())
            return

        iptos = get_param(setup, 'iptos')

        nvp = \
            [   
                ('Source',get_param(setup,'ipSrc')),
                ('Destination',get_param(setup,'ipDest')),
                ('Default Gateway',get_param(setup,'ipGateway')),
                ('Subnet Mask',get_param(setup, 'subnetMask', '255.255.255.0')),
                ('IP Version',get_param(setup, 'versionAndLength')>>4),
                ('Protocol', get_param(setup, 'protocol')),
                ('Type of Service', iptos)
            ]
        tos = get_param(setup, 'tos')

        if iptos == 'RFC1349':
            precedence = tos>>5
            nvp.append(('Precedence', precedence))
            nvp.append(('Type of Service', hex((tos>>1)&0x0F)))
            nvp.append(('MBZ', tos & 0x01))
        else:
            nvp.append(('DSCP', int_to_hex(tos>>2, 2, True)))
            nvp.append(('Currently Unused', (tos & 0x03)))

        nvp.append(('Header Length',get_param(setup, 'versionAndLength')&0x0F))
        nvp.append(('Identifier', int_to_hex(setup['identifier'], 4, True)))

        fragFlagsAndOffset = get_param(setup, 'fragFlagsAndOffset')
        nvp.append(('Flag Don\'t Fragment', (fragFlagsAndOffset>>14)&0x01))
        nvp.append(('Flag More Fragment', (fragFlagsAndOffset>>13)&0x01))
        nvp.append(('Fragment Offset', fragFlagsAndOffset&0x1FFF))
        nvp.append(('Time To Live', get_param(setup, 'timeToLive')))

        # Stream IP Options
        if get_param(setup, 'enipopt') != 0:
            optlen = get_param(setup, 'optlen')
            nvp.append(('Length of IP Option', optlen))
            opt_data = setup['optdata'];
            num = 0
            for opt in opt_data:
                num = num + 1
                nvp.append(('Option Data %d' % num, int_to_hex(opt, 8, True)))
                if num >= optlen:
                    break
        else:
            nvp.append(('IP Option', 'Disable'))
            
        stream_ip_table = []
        if format == 'pdf':
            for n,v in nvp:
                stream_ip_table.append([n,v])
        else:
            stream_ip_table = nvp

        return stream_ip_table        

    def getRFC2544StreamMplsConfig(self, streamTable, format):
        try:
            setup = streamTable['mplsCfg']
        except:
            self.write_log('Throughput Mpls setup data not found!', 'Error', sys.exc_info())
            return
        
        num_mpls = len(setup)
        
        stream_mpls_setup = []
        if format == 'pdf':
            names = ['ID','Experimental','Bottom of Stack','Time to Live']
        else:
            names = ["ID","Experimental","Bottom of Stack","Time to Live"]
        stream_mpls_setup.append(names)

        for mpls in setup:
            values = \
                [
                    get_param(mpls, 'hopLabel'),
                    get_param(mpls, 'exp'),
                    get_param(mpls, 'eofStack'),
                    get_param(mpls, 'timeToLive')
                ]
            stream_mpls_setup.append(values)
        return stream_mpls_setup

    def getRFC2544StreamUdpConfig(self, streamTable, format):
        try:
            setup = streamTable['udpHeader']
        except:
            self.write_log('RFC2544 StreamUdpConfig data not found!', 'Error', sys.exc_info())
            return
        
        nvp = \
                [
                    ('Source Port', get_param(setup, 'SrcPort')),
                    ('Destination Port', get_param(setup, 'DestPort'))
                ]
        stream_udp_table = []
        if format == 'pdf':
            for n,v in nvp:
                stream_udp_table.append([n,v])
        else:
            stream_udp_table = nvp
            
        return stream_udp_table

    def getRFC2544StreamTcpConfig(self, streamTable, format):
        try:
            setup = streamTable['tcpHeader']
        except:
            self.write_log('RFC2544 StreamTcpConfig data not found!', 'Error', sys.exc_info())
            return
        nvp = \
                [
                    ('Source Port', get_param(setup, 'SrcPort')),
                    ('Destination Port',get_param(setup, 'DestPort')),
                    ('Sequence Number',hex(get_param(setup, 'SeqNum'))),
                    ('ACK Number',hex(get_param(setup, 'AckNum'))),
                    ('Data Offset',altbin((get_param(setup, 'OffsetResFlags')>>12)&0x0F)),
                    ('Reserved 6 bits',altbin((get_param(setup, 'OffsetResFlags')>>6)&0x3F)),
                    ('Window Size',hex(get_param(setup, 'WinSize'))),
                    ('Urgent Pointer',hex(get_param(setup, 'UrgentPtr'))),
                    ('URG',(get_param(setup, 'OffsetResFlags')>>5)&0x01),
                    ('ACK',(get_param(setup, 'OffsetResFlags')>>4)&0x01),
                    ('PSH',(get_param(setup, 'OffsetResFlags')>>3)&0x01),
                    ('RST',(get_param(setup, 'OffsetResFlags')>>2)&0x01),
                    ('SYN',(get_param(setup, 'OffsetResFlags')>>1)&0x01),
                    ('FIN',(get_param(setup, 'OffsetResFlags')&0x01)),
                ]    
        stream_tcp_table = []
        if format == 'pdf':
            for n,v in nvp:
                stream_tcp_table.append([n,v])
        else:
            stream_tcp_table = nvp
        
        return stream_tcp_table

    def getRFC2544PayloadConfig(self, streamTable, format):
        setup = streamTable['pattern']
        self.snts = True
        pattern_type = get_param(setup, 'type')

        pattern_invert = 'Off'
        if setup['invert'] == 1: pattern_invert = 'On'
        
        nvp = \
        [ 
            ('Pattern Type',pattern_type)
        ]
        
        if pattern_type == 'USER':
            nvp.append( ('User Pattern Type',self.get_cmd_param(rfc_cmd_list,'SET-RFC2544-USERPAT','userpat')) )
            nvp.append( ('User Pattern',hex(self.get_cmd_param(rfc_cmd_list,'SET-RFC2544-USERPAT','patdata')).rstrip('L')) )            
        elif pattern_type == 'USER1024':
            for i in range(1,33):
                nvp.append( ('Pattern Data %d'%i, hex(self.get_cmd_param(rfc_cmd_list,'SET-RFC2544-USERPAT','patdata%d'%i)).rstrip('L')) )        
        elif pattern_type in ('ALL1','ALL0','ALT1'):
            pass
        else:
            nvp.append(('Invert', pattern_invert))            
            
        stream_payload_table = []
        if format == 'pdf':
            for n,v in nvp:
                stream_payload_table.append([n,v])
        else:
            stream_payload_table = nvp
            
        return stream_payload_table

    def rfc2544Summary(self, fd, meas_data, format):
        try:
            events = meas_data['rfc2544_event']
            test = events[0]['event']
            results = meas_data['result_rfc2544']
        except:
            self.write_log('RFC2544 Latency result data not found!', 'Error', sys.exc_info())
            return
        
        seq_types = ['Throughput', 'Latency', 'Frame Loss', 'Back to Back']

        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            table.append(['Sequence No.', 'Test Type', 'Size', 'Rate', 'Frames', 'Status'])
        else:
            makeTable = self.createCsvTable
            table.append(["Sequence No.", "Test Type", "Size", "Rate", "Frames", "Status"])

        tstatus = ['Pass', 'Fail', 'In Progress', 'N/A', 'Linkdown', 'Done', 'Stopped']
        ostatus = ['Complete', 'Fail', 'In Progress', 'N/A', 'Linkdown', 'Done', 'Stopped']

        pageNo = 0
        total = get_param(events[pageNo]['event'], 'total')
        index = 0
        pos = 0
        prev_latency_snum = -1
        while pos < total - 1:
            try:
                if index == page_size: # go to begin of next page
                    pageNo += 1
                    index = 0
                seq = events[pageNo]['event'][str(index)]
                '''
                if get_param(seq, 'testStage') != 0:
                    index += 1
                    pos += 1
                    continue
                '''
                row = []
                seq_type = get_param(seq, 'testMode')
                if seq_type == 0:#throughput
                    status = tstatus[get_param(seq, 'status')]
                else:
                    status = ostatus[get_param(seq, 'status')]
                sequence_num = get_param(seq,'sequenceNum')
                if seq_type == 1:
                    if sequence_num == prev_latency_snum:
                        index += 1
                        pos += 1
                        continue
                    prev_latency_snum = sequence_num
            
                if seq_type == 3: #backtoBack
                    frames = get_param(seq,'frameCur')
                else :
                    frames = get_param(seq,'resolutionFrame')
                row.extend([
                    sequence_num,
                    seq_types[seq_type],
                    get_param(seq,'streamSize'),
                    get_param(seq,'frameRate'),
                    frames,
                    status
                    ])
                table.append(row)
            except:
                self.write_log('', 'Error', sys.exc_info())
                break
            index += 1
            pos += 1
        makeTable(fd, 'Summary of Tests', table)

    def rfc2544LatencyTable(self, fd, meas_data, format):            
        try:
            events = meas_data['rfc2544_event']
            test = events[0]['event']
            results = meas_data['result_rfc2544']
            rfccfg = meas_data['config']['config']['ether']['stR2544Config']
        except:
            self.write_log('RFC2544 Latency result data not found!')
            return
        flag = 0
        if format == 'pdf':
            makeTable = self.createPdfTable
            table = [['Frame Size\n(bytes)', 'Throughput', '', 'Latency', '', '', '', '']]
            avg_string = Paragraph('<para><font>Avg (&#181;s)</font></para>', styleSheet['Normal']).getPlainText()
            min_string = Paragraph('<para><font>Min (&#181;s)</font></para>', styleSheet['Normal']).getPlainText()
            max_string = Paragraph('<para><font>Max (&#181;s)</font></para>', styleSheet['Normal']).getPlainText()
            table.append(['', 'Percentage', 'Threshold Status', \
                          'Percentage', avg_string, min_string, max_string, 'Threshold Status'])
        else:
            makeTable = self.createCsvTable
            table = []
            table.append(["Frame Size","Throughput Percentage","Throughput Threshold Status", \
                          "Latency Percentage","Latency Avg (us)","Latency Min (us)","Latency Max (us)", \
                          "Latency Threshold Status"])
        
        status = ['Pass', 'Fail', 'In Progress', 'N/A', 'Linkdown', 'Done', 'Stopped']

        quick_Latency = False
        pageNo = 0
        total = get_param(events[pageNo]['event'], 'total')
        index = 0
        pos = 0
        threshold_on = rfccfg['frame']['thresholdOn']
        
        while pos < total - 1:
            if index == page_size:
                pageNo += 1
                index = 0
            seq = events[pageNo]['event'][str(index)]
            testMode = get_param(seq, 'testMode')
            if  testMode != 0 or get_param(seq, 'testStage') != 0:
                index += 1
                pos += 1
                continue
            flag = 1
            row = []

            row.extend([get_param(seq, 'streamSize'), 
                        get_param(seq, 'passRate'), 
                        status[seq['thresholdThroughput']]
                        ])

            # for quick Latency mode    
            if get_param(seq, 'quickLatencyMode', 0) > 0:                    
                quick_Latency = True
                checkNA = seq['latencyMax']
                row.extend([
                            get_param(seq, 'passRate'),
                            get_param(seq, 'latencyAvg') if checkNA >= 0 else "N/A",
                            get_param(seq, 'latencyMin') if checkNA >= 0 else "N/A",
                            get_param(seq, 'latencyMax') if checkNA >= 0 else "N/A",
                            status[seq['thresholdLatency']]
                           ])
            else:
                row.extend(['', '', '', '', ''])
        
            table.append(row)
            index += 1
            pos += 1
 
        # for normal Latency  
        if not quick_Latency:
            pageNo = 0
            index = 0
            pos = 0
            if format == 'pdf':
                lat_index = 1
            else:
                lat_index = 0

            while pos < total - 1:
                if index == page_size:
                    pageNo += 1
                    index = 0
                seq = events[pageNo]['event'][str(index)]
                if get_param(seq, 'testMode') != 1 or get_param(seq, 'testStage') != 0:
                    index += 1
                    pos += 1
                    continue
                flag = 1
                lat_index += 1
                if lat_index == len(table):
                    table.append(['','','','', '', '', '', '']) 
                    table[lat_index][0] = get_param(seq, 'streamSize')

                checkNA = seq['latencyMax']
                table[lat_index][3] = get_param(seq, 'frameRate')
                table[lat_index][4] = get_param(seq, 'latencyAvg') if checkNA >= 0 else "N/A"
                table[lat_index][5] = get_param(seq, 'latencyMin') if checkNA >= 0 else "N/A"
                table[lat_index][6] = get_param(seq, 'latencyMax') if checkNA >= 0 else "N/A"
                table[lat_index][7] = status[seq['thresholdLatency']]

                index += 1
                pos += 1
                
        style=[ \
            ('GRID',(0,0),(-1,-1),0.5, colors.grey),
            ('BOX',(0,0),(-1,-1),1, colors.grey),
            ('SPAN',(0, 0),(0, 1)),
            ('SPAN',(1,0),(2,0)),
            ('SPAN',(3,0),(7,0)),
            ('ALIGN',(0,0),(7,1),'CENTER'),
            ('VALIGN',(0,0),(0,0),'MIDDLE'),
            ('BACKGROUND', (0,0), (-1, -1), colors.lavender),
            ]

        if len(table) == 2:            
            no_data_row = ['No Data available', '', '', '', '', '', '',]
            style.append(('SPAN', (0, 2), (7, 2)))
            table.append(no_data_row)
        
        if flag == 0:
            return
        makeTable(fd, "Throughput - Latency Table", table, style)
        

    def rfc2544FrameLossTable(self, fd, meas_data, format):
        try:
            events = meas_data['rfc2544_event']
            test = events[0]['event']
            results = meas_data['result_rfc2544']
        except:
            self.write_log('RFC2544 FrameLoss result data not found!', 'Error', sys.exc_info())
            return
        flag = 0
        try:            
            is_frameloss_on = results['is_frameloss_on']
            if not is_frameloss_on:
                self.write_log('frameloss must be ON!', 'Error')
                return
        except:
            self.write_log('RFC2544 frameLoss chart data error!', 'Error', sys.exc_info())
            return

        if format == 'pdf':
            makeTable = self.createPdfTable
        else:
            makeTable = self.createCsvTable
            
        table = \
        [
         ['Input\nRate (%)', 'Frame Loss Rate %'],
         ['']
        ]

        pageNo = 0
        total = get_param(events[pageNo]['event'], 'total')
        index = 0
        pos = 0
        old_rate = -100
        frame_line = table[1]
        current_line = []
        while pos < total - 1:
            if index == page_size:
                pageNo += 1
                index = 0
            seq = events[pageNo]['event'][str(index)]
            if get_param(seq, 'testMode') != 2: 
                index += 1
                pos += 1
                continue
            flag = 1
            current_rate = get_param(seq, 'frameRate')
            if old_rate != current_rate:
                if len(current_line) > 1:                        
                    table.append(current_line)                
                current_line = [current_rate]                
                old_rate = current_rate
                
            stream_size = get_param(seq, 'streamSize')
            if stream_size not in frame_line:
                frame_line.append(stream_size)
            if seq['frameLossRate'] < 0.0:
                seq['frameLossRate'] = 0.0
            frameloss_rate = get_param(seq, 'frameLossRate', CNA)
            current_line.append(frameloss_rate)
            
            index += 1
            pos += 1
                
        row_len = len(table[1])
        if row_len < 2: row_len = 2        
        
        table[0].extend([''] * (row_len - 2))
        
        style = \
        [ 
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0),(-1, -1), 1, colors.grey),
            ('SPAN', (0, 0), (0, 1)),
            ('SPAN', (1, 0), (row_len - 1, 0)),
            ('ALIGN', (1, 0), (row_len -1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (0, 1), 'TOP'),
            ('BACKGROUND', (0,0), (-1, -1), colors.lavender),
        ]
        
        if len(current_line) > 1:
            table.append(current_line)
        
        if len(table) == 2:
            table[1] = ['', 'No Data available']

        for row in table:
            line_len = len(row)
            row.extend([''] * (row_len - line_len))

        if flag == 0:
            return
        
        makeTable(fd, "Frame Loss Table", table, style)

    def rfc2544Back2BackTable(self, fd, meas_data, format):
        try:
            events = meas_data['rfc2544_event']
            test = events[0]['event']
            results = meas_data['result_rfc2544']
        except:
            self.write_log('RFC2544 Back2Back result data not found!', 'Error', sys.exc_info())
            return
        flag = 0
        if format == 'pdf':
            makeTable = self.createPdfTable
        else:
            makeTable = self.createCsvTable
            
        table = []
        table.append(["Frame Size (bytes)","Average","Minimum","Maximum"])

        fs = {}
        
        pageNo = 0
        total = get_param(events[pageNo]['event'], 'total')
        index = 0
        pos = 0
        while pos < total - 1:
            if index == page_size:
                pageNo += 1
                index = 0
            seq = events[pageNo]['event'][str(index)]
            if get_param(seq, 'testMode') != 3:
                index += 1
                pos += 1
                continue
            flag = 1
            ss = get_param(seq, 'streamSize')
            row = \
            [
                ss,
                curnum_to_string(long(seq['frameAvg']), True),
                get_param(seq,'frameMin', ICNA),
                get_param(seq,'frameMax', ICNA)
                #get_param(seq,'status')
            ]

            if ss in fs:
                table[fs[ss]] = row
                index += 1
                pos += 1
                continue

            table.append(row)    
            fs[ss] = table.index(row)

            index += 1
            pos += 1
            
        if flag == 0:
            return
        makeTable(fd, "Back to Back Table", table)
                
    def monitorSetup(self, fd, config, format):
        try:
            setup = config['config']['ether']['stMonitorConfig']
        except:
            self.write_log('Monitor setup data not found!', 'Error', sys.exc_info())
            return
        
        primaryPortID = get_param(setup, 'primary_port')               
        secondaryPortID = get_param(setup, 'secondary_port')

        if primaryPortID != NA:
            primaryPortID = 'P%d' % (primaryPortID + 1)         
        if secondaryPortID != NA:
            secondaryPortID = 'P%d' % (secondaryPortID + 1)

        self.primaryPortID = primaryPortID
        self.secondaryPortID = secondaryPortID
            
        if format == 'pdf':
            makeTable = self.createPdfTable
            primary_name = 'Primary Port'
            secondary_name = 'Secondary Port'
            
            if primaryPortID != secondaryPortID:
                table = [ 
                            [primary_name,primaryPortID],
                            [secondary_name,secondaryPortID],
                        ]
                table_name = "Dual Port Monitor Test"
            else:
                table = [ 
                            [primary_name,primaryPortID]
                        ]
                table_name = "Single Port Monitor Test"
        else:
            makeTable = self.createCsvTable
            primary_name = "Primary Port"
            secondary_name = "Secondary Port"
            if primaryPortID is not secondaryPortID:
                table = [ 
                            [primary_name,secondary_name],
                            [primaryPortID,secondaryPortID],
                        ]
                table_name = "Dual Port Monitor Test"
            else:
                table = [ 
                            [primary_name,secondary_name],
                            [primaryPortID,NA],
                        ]
                table_name = "Single Port Monitor Test"
        
        makeTable(fd, table_name, table)

    def summaryTable(self, fd, params, format):
        summ = {}
        sum2 = {}
        try:
            if self.test_mode == 'MONITOR' and self.primaryPortID != self.secondaryPortID:
                summ = params['result_monitor']['primary']
                sum2 = params['result_monitor']['secondary']
            elif self.test_mode == 'LOOPBACK':
                summ = params['result_loopback']['result']
            elif self.test_mode == 'RFC2544':
                summ = params['result_rfc2544']['result']
            elif self.test_mode == 'IP':
                summ = params['result_iptest']['result']
            elif self.test_mode == 'Y156SAM':
                summ = params['result_y156sam']['result']
            elif self.test_mode == 'THROUGHPUT':
                results = params['result'][0]
                summ = results['eth']
                sum2 = results['eth']
                try:
                    setup = params['config']['config']['ether']['stBertConfig']
                    test_layer = get_param(setup, 'testLayer')
                except:
                    self.write_log('THROUGHPUT setup data not found!', 'Error', sys.exc_info())
                    return
        except:
            self.write_log('Summary Table data not found!', 'Error', sys.exc_info())
            return
        
        if self.test_mode == 'THROUGHPUT' and test_layer == 'L1UNFRAME':
            nvpq = \
                [                
                    ('TX Utilized Line Rate (%)',       get_param_from_path(summ, 'txStats/totalBytes', 'dummy', NA),  get_param_from_path(sum2, 'txStats/totalBytes', 'curUtil', NNA)),
                    fbps4('TX Utilized Line Rate (%s)', get_param_from_path(summ, 'txStats', 'lineRate', NNA, False),  get_param_from_path(sum2, 'txStats', 'lineRate', NNA, False)),
                    fbps4('TX Information Rate (%s)',        get_param_from_path(summ, 'txStats', 'dummy', NA),             get_param_from_path(sum2, 'txStats', 'dataRate', NNA)),
                    ('TX Frame Rate (fps)',             get_param_from_path(summ, 'txStats/totalFrames', 'dummy', NA), get_param_from_path(sum2, 'txStats/totalFrames', 'curRate', NNA)),
                    ('RX Utilized Line Rate (%)',       get_param_from_path(summ, 'rxStats/totalBytes', 'dummy', NA),  get_param_from_path(sum2, 'rxStats/totalBytes', 'curUtil', NNA)),
                    fbps4('RX Utilized Line Rate (%s)', get_param_from_path(summ, 'rxStats', 'lineRate', NNA, False),         get_param_from_path(sum2, 'rxStats', 'lineRate', NNA, False)),
                    fbps4('RX Information Rate (%s)',        get_param_from_path(summ, 'rxStats', 'dummy', NA),             get_param_from_path(sum2, 'rxStats', 'dataRate', NNA)),
                    ('RX Frame Rate (fps)',             get_param_from_path(summ, 'rxStats/totalFrames', 'dummy', NA), get_param_from_path(sum2, 'rxStats/totalFrames', 'curRate', NNA)),                
                ]
        elif self.test_mode == 'MONITOR':
            nvpq = \
                [                
                    ('TX Utilized Line Rate (%)',       NA, NA),
                    ('TX Utilized Line Rate (%s)',      NA, NA),
                    ('TX Information Rate (%s)',        NA, NA),
                    ('TX Frame Rate (fps)',             NA, NA),
                    ('RX Utilized Line Rate (%)',       get_param_from_path(summ, 'rxStats/totalBytes', 'curUtil'),      get_param_from_path(sum2, 'rxStats/totalBytes', 'curUtil', NNA)),
                    fbps4('RX Utilized Line Rate (%s)', get_param_from_path(summ, 'rxStats', 'lineRate', NNA, False),    get_param_from_path(sum2, 'rxStats', 'lineRate', NNA, False)),
                    fbps4('RX Information Rate (%s)',   get_param_from_path(summ, 'rxStats', 'dataRate', NNA, False),    get_param_from_path(sum2, 'rxStats', 'dataRate', NNA, False)),
                    ('RX Frame Rate (fps)',             get_param_from_path(summ, 'rxStats/totalFrames', 'curRate', NNA),get_param_from_path(sum2, 'rxStats/totalFrames', 'curRate', NNA)),                
                ]
        elif self.test_mode != 'Y156SAM':
            nvpq = \
                [                
                    ('TX Utilized Line Rate (%)',       get_param_from_path(summ, 'txStats/totalBytes', 'curUtil', NNA), get_param_from_path(sum2, 'txStats/totalBytes', 'curUtil', NNA)),
                    fbps4('TX Utilized Line Rate (%s)', get_param_from_path(summ, 'txStats', 'lineRate', NNA, False),    get_param_from_path(sum2, 'txStats', 'lineRate', NNA, False)),
                    fbps4('TX Information Rate (%s)',   get_param_from_path(summ, 'txStats', 'dataRate', NNA, False),    get_param_from_path(sum2, 'txStats', 'dataRate', NNA, False)),
                    ('TX Frame Rate (fps)',             get_param_from_path(summ, 'txStats/totalFrames', 'curRate', NNA),get_param_from_path(sum2, 'txStats/totalFrames', 'curRate', NNA)),
                    ('RX Utilized Line Rate (%)',       get_param_from_path(summ, 'rxStats/totalBytes', 'curUtil'),      get_param_from_path(sum2, 'rxStats/totalBytes', 'curUtil', NNA)),
                    fbps4('RX Utilized Line Rate (%s)', get_param_from_path(summ, 'rxStats', 'lineRate', NNA, False),    get_param_from_path(sum2, 'rxStats', 'lineRate', NNA, False)),
                    fbps4('RX Information Rate (%s)',   get_param_from_path(summ, 'rxStats', 'dataRate', NNA, False),    get_param_from_path(sum2, 'rxStats', 'dataRate', NNA, False)),
                    ('RX Frame Rate (fps)',             get_param_from_path(summ, 'rxStats/totalFrames', 'curRate', NNA),get_param_from_path(sum2, 'rxStats/totalFrames', 'curRate', NNA)),                
                ]
        else : nvpq = []
        
        if self.test_mode == 'Y156SAM' and self.interface == 'RJ45':
            return

        transceiverInfo = None
        if self.test_mode == 'RFC2544' and params['result_rfc2544']['result']['p1TransceiverInfo'] and params['result_rfc2544']['result']['p2TransceiverInfo']:
            summ = params['result_rfc2544']['result']
            sum2 = summ
            nvpq.append(('Vendor',                  get_param_from_path(summ, 'p1TransceiverInfo', 'vendor_name'),    get_param_from_path(sum2, 'p2TransceiverInfo', 'vendor_name')))
            nvpq.append(('Wavelength (nm)',         get_param_from_path(summ, 'p1TransceiverInfo', 'wavelength'),     get_param_from_path(sum2, 'p2TransceiverInfo', 'wavelength')))  
            nvpq.append(('Rx Power (micro watts)',  get_param_from_path(summ, 'p1TransceiverInfo', 'rxpwruw', NNA),        get_param_from_path(sum2, 'p2TransceiverInfo', 'rxpwruw')))
            nvpq.append(('Rx Power (dBm)',          get_param_from_path(summ, 'p1TransceiverInfo', 'rxpwrbm', NNA),        get_param_from_path(sum2, 'p2TransceiverInfo', 'rxpwrbm')))
        elif self.test_mode == 'Y156SAM' and params['result_y156sam']['result']['p1TransceiverInfo'] and params['result_y156sam']['result']['p2TransceiverInfo']:
            summ = params['result_y156sam']['result']
            sum2 = summ
            nvpq.append(('Vendor',                  get_param_from_path(summ, 'p1TransceiverInfo', 'vendor_name'),    get_param_from_path(sum2, 'p2TransceiverInfo', 'vendor_name')))
            nvpq.append(('Wavelength (nm)',         get_param_from_path(summ, 'p1TransceiverInfo', 'wavelength'),     get_param_from_path(sum2, 'p2TransceiverInfo', 'wavelength')))  
            nvpq.append(('Rx Power (micro watts)',  get_param_from_path(summ, 'p1TransceiverInfo', 'rxpwruw', NNA),        get_param_from_path(sum2, 'p2TransceiverInfo', 'rxpwruw')))
            nvpq.append(('Rx Power (dBm)',          get_param_from_path(summ, 'p1TransceiverInfo', 'rxpwrbm', NNA),        get_param_from_path(sum2, 'p2TransceiverInfo', 'rxpwrbm')))
        else:
            nvpq.append(('Vendor',                  get_param_from_path(summ, 'transceiverInfo', 'vendor_name'),    get_param_from_path(sum2, 'transceiverInfo', 'vendor_name')))
            nvpq.append(('Wavelength (nm)',         get_param_from_path(summ, 'transceiverInfo', 'wavelength'),     get_param_from_path(sum2, 'transceiverInfo', 'wavelength')))  
            nvpq.append(('Rx Power (micro watts)',  get_param_from_path(summ, 'transceiverInfo', 'rxpwruw', NNA),        get_param_from_path(sum2, 'transceiverInfo', 'rxpwruw', NNA)))
            nvpq.append(('Rx Power (dBm)',          get_param_from_path(summ, 'transceiverInfo', 'rxpwrbm', NNA),        get_param_from_path(sum2, 'transceiverInfo', 'rxpwrbm', NNA)))
        
        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            
            if self.test_mode == 'MONITOR' and self.primaryPortID != self.secondaryPortID:            
                table.append(['Port', self.primaryPortID, self.secondaryPortID])
                for n, v1, v2 in nvpq:
                    table.append([n, v1, v2])
            else:
                for n, v, unused in nvpq:
                   table.append([n, v])
        else:
            makeTable = self.createCsvTable
            if self.test_mode == 'MONITOR' and self.primaryPortID != self.secondaryPortID:            
                table.append(['Port', self.primaryPortID, self.secondaryPortID])
                for n, v1, v2 in nvpq:
                    table.append([n, v1, v2])
            else:
                for n, v, unused in nvpq:
                   table.append([n, v])
                
        makeTable(fd, "Summary Data", table)

    def summaryTableFC_FC1(self, fd, params, format):
        """Writes Measurement Summary Information
           @type  fd: report object
           @param params: 'JSONObject'
           @param format: 'pdf' or 'csv'
        """
        if self.test_mode == 'FC_BERT':
            summ = params['result_fc_bert']['result']
            txStatus = summ['tx']['txFrameStats']
            rxStatus = summ['rx']['rxFrameStats']

        nvpq = \
            [
                ('TX Utilized Line Rate (kbps)',      get_param(txStatus, 'lineRate', ICNA)),
                ('RX Utilized Line Rate (kbps)',      get_param(rxStatus, 'lineRate', ICNA)),
            ]
        transceiverInfo = summ['transceiverInfo']
        nvpq.append(('Vendor',                  get_param_from_path(summ, 'transceiverInfo', 'vendor_name')))
        nvpq.append(('Wavelength (nm)',         get_param_from_path(summ, 'transceiverInfo', 'wavelength')))  
        nvpq.append(('RX Power (micro watts)',  get_param_from_path(summ, 'transceiverInfo', 'rxpwruw', FNA)))
        nvpq.append(('RX Power (dBm)',          get_param_from_path(summ, 'transceiverInfo', 'rxpwrbm', FNA)))
        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n, v in nvpq:
               table.append([n, v])
        else:
            makeTable = self.createCsvTable
            for n, v in nvpq:
               table.append([n, v])
        makeTable(fd, "Summary Data", table)

        
    def summaryTableFC(self, fd, params, format):
        """Writes Measurement Summary Information
           @type  fd: report object
           @param params: 'JSONObject'
           @param format: 'pdf' or 'csv'
        """
        if self.test_mode == 'FC_BERT':
            summ = params['result_fc_bert']['result']
            txStatus = summ['tx']['txFrameStats']
            rxStatus = summ['rx']['rxFrameStats']
        elif self.test_mode == 'FC_LOOPBACK':
            summ = params['result_fc_loopback']['result']
            txStatus = summ['txStats']
            rxStatus = summ['rxStats']
        elif self.test_mode == 'FC_RFC2544':
            summ = params['result_fc_rfc2544']['result']
            txStatus = summ['txStats']
            rxStatus = summ['rxStats']
        elif self.test_mode == 'FC_B2B':
            summ = params['result_fc_b2b']['result']
            txStatus = summ['tx']['txFrameStats']
            rxStatus = summ['rx']['rxFrameStats']
            
        result_capture = params['result_capture']['result']
        capture_status = get_param(result_capture, 'status', NA)
        if capture_status == 'COMPLETE':
            capture_status = 'Complete'
        elif capture_status == 'NOT_STARTED':
            capture_status = 'No Capture'
        elif capture_status == 'IN_PROGRESS':
            capture_status = 'In Progress'
        else:
            capture_status = 'Unknow Error'

        nvpq = \
            [
                ('TX Utilized Line Rate (%)',   get_param(txStatus['totalBytes'], 'curUtil', FNA)),
                ('TX Utilized Line Rate (kbps)',      get_param(txStatus, 'lineRate', ICNA)),
                ('TX Information Rate (kbps)',      get_param(txStatus, 'dataRate', ICNA)),
                ('TX Frame Rate (fps)',     get_param(txStatus['totalFrames'], 'curRate', FNA)),

                ('RX Utilized Line Rate (%)',   get_param(rxStatus['totalBytes'], 'curUtil', FNA)),
                ('RX Utilized Line Rate (kbps)',      get_param(rxStatus, 'lineRate', ICNA)),
                ('RX Information Rate (kbps)',      get_param(rxStatus, 'dataRate', ICNA)),
                ('RX Frame Rate (fps)',     get_param(rxStatus['totalFrames'], 'curRate', FNA)),

                ('Capture Status',     capture_status),
                ('Capture Packets',     get_param(result_capture, 'noPcap', NNA)),
            ]
        transceiverInfo = summ['transceiverInfo']
        nvpq.append(('Vendor',                  get_param_from_path(summ, 'transceiverInfo', 'vendor_name')))
        nvpq.append(('Wavelength (nm)',         get_param_from_path(summ, 'transceiverInfo', 'wavelength', ICNA)))  
        nvpq.append(('RX Power (micro watts)',  get_param_from_path(summ, 'transceiverInfo', 'rxpwruw', FNA)))
        nvpq.append(('RX Power (dBm)',          get_param_from_path(summ, 'transceiverInfo', 'rxpwrbm', FNA)))
        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n, v in nvpq:
               table.append([n, v])
        else:
            makeTable = self.createCsvTable
            for n, v in nvpq:
               table.append([n, v])
        makeTable(fd, "Summary Data", table)

    def aggregateTable(self, fd, params, format):
        """Writes Aggregate Result Table
           @type  fd: Report File Object
           @param fd: Descriptor to current report object
           @param params: Table data
           @type  format: String 
           @param format: 'pdf' or 'csv'
        """
        
        if self.test_mode == 'RFC2544':
            try:
                results = params['result_rfc2544']['result']
            except:
                self.write_log('RFC2544 setup data not found!', 'Error', sys.exc_info())
                return
        elif self.test_mode == 'IP':
            try:
                results = params['result_iptest']['result']
            except:
                self.write_log('IPTEST setup data not found!', 'Error', sys.exc_info())
                return
        elif self.test_mode == 'LOOPBACK':
            try:
                results = params['result_loopback']['result']
            except:
                self.write_log('LOOPBACK setup data not found!', 'Error', sys.exc_info())
                return
        elif self.test_mode == 'MONITOR':
            try:
                if self.primaryPortID == self.secondaryPortID:
                    results = params['result_monitor']['primary']
                    results['txStats'] = {}
                    results['txError'] = {}
                else:
                    results = params['result_monitor']['secondary']
                    results['txStats'] = params['result_monitor']['primary']['rxStats']
                    results['txError'] = params['result_monitor']['primary']['rxError']
            except:
                self.write_log('MONITOR setup data not found!', 'Error', sys.exc_info())
                return
        else:
            try:
                setup = params['config']['config']['ether']['stBertConfig']
                test_layer = get_param(setup, 'testLayer')                    
                results = params['result'][0]['eth']
            except:
                self.write_log('THROUGHPUT setup data not found!', 'Error', sys.exc_info())
                return
        try:
            resRx = results['rxStats']
            resTx = results['txStats']
        except:
            self.write_log('No Aggregate Stats Data', 'Error', sys.exc_info())
            resRx = {}
            resTx = {}
        
        try:
            errRx = results['rxError']
            errTx = results['txError']
        except:
            self.write_log('No Aggregate Error Data', 'Error', sys.exc_info())
            errRx = {}
            errTx = {}
            
        # layer 1   
        # Defect Data only
        if self.test_mode == 'THROUGHPUT' and test_layer == 'L1UNFRAME':
            nv_error = \
            [                    
                ['Current Bit',             get_param(errRx['bitError'], 'current', ICNA)], 
                ['Bit Error',               get_param(errRx['bitError'], 'total', ICNA)], 
                ['Current Bit Error Rate',  get_param(errRx['bitError'], 'curBitRate', EXP)],
                ['Bit Error Rate',          get_param(errRx['bitError'], 'bitRate', EXP)], 
                ['LOPS (secs)',             get_param(errRx['bitError'], 'lopsTime', NNA)], 
            ]            
            
            nv_loss = \
            [
                ['LOS Event',               get_param(errRx['los'], 'total', ICNA)], 
                ['LOSS Aggregate (secs)',   get_param(errRx['los'], 'time', NNA)], 
                ['LOSS Minimum (secs)',     get_param(errRx['los'], 'min', NNA)], 
                ['LOSS Maximum (secs)',     get_param(errRx['los'], 'max', NNA)], 
                ['LOSS Current (secs)',     get_param(errRx['los'], 'cur', NNA)], 
                ['LOSS Average (secs)',     get_param(errRx['los'], 'avg', NNA)],
            ]
            
            table = []
            style = []
            colwidths = None
            if format == 'pdf':
                style= \
                [
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('BOX', (0,0), (-1,-1), 1, colors.grey),
                    ('BACKGROUND', (0,0), (-1, -1), colors.lavender),
                    ('SPAN', (0, 0), (1, 0)),
                    ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                    ('SPAN', (0, 6), (1, 6)),
                    ('ALIGN', (0, 6), (1, 6), 'CENTER')
                ]
                colwidths = [2.4 * inch, 2.4 * inch]
                
                makeTable = self.createPdfTable
                table.append(['Data Error (Count)', ''])
                table.extend(nv_error)
                table.append(['Alarm (Count)', ''])
                table.extend(nv_loss)
            else:       
                makeTable = self.createCsvTable
                names = ['Data Error (Count)', '', 'Alarm (Count)', '']
                table.append(names)
                nv_error.extend([['', '']])
                index = 0
                for line in nv_error:
                    line.extend(nv_loss[index])
                    table.append(line)
                    index += 1
            makeTable(fd, 'Defect', table, style, colwidths)
            return
        
        # layer 2
        # ( Description, Tx Param Name, Rx Param Name )
        nvp = \
        [
            ('Total Frames',                    get_param(resTx['totalFrames'], 'total', ICNA),   get_param(resRx['totalFrames'], 'total', ICNA), True), 
            ('Total Bytes',                     get_param(resTx['totalBytes'], 'total', ICNA),    get_param(resRx['totalBytes'], 'total', ICNA), True), 
            ('Frame Rate Current (fps)',        get_param(resTx['totalFrames'], 'curRate', CNA), get_param(resRx['totalFrames'], 'curRate', CNA), False), 
            ('Frame Rate Average (fps)',        get_param(resTx['totalFrames'], 'avgRate', CNA), get_param(resRx['totalFrames'], 'avgRate', CNA), False),  
            ('Frame Rate Minimum (fps)',        get_param(resTx['totalFrames'], 'minRate', CNA), get_param(resRx['totalFrames'], 'minRate', CNA), False),  
            ('Frame Rate Maximum (fps)',        get_param(resTx['totalFrames'], 'maxRate', CNA), get_param(resRx['totalFrames'], 'maxRate', CNA), False), 
            ('Utilized Line Rate Current (%)',  get_param(resTx['totalBytes'], 'curUtil', NNA),  get_param(resRx['totalBytes'], 'curUtil', NNA), False), 
            ('Utilized Line Rate Average (%)',  get_param(resTx['totalBytes'], 'avgUtil', NNA),  get_param(resRx['totalBytes'], 'avgUtil', NNA), False), 
            ('Utilized Line Rate Minimum (%)',  get_param(resTx['totalBytes'], 'minUtil', NNA),  get_param(resRx['totalBytes'], 'minUtil', NNA), False), 
            ('Utilized Line Rate Maximum (%)',  get_param(resTx['totalBytes'], 'maxUtil', NNA),  get_param(resRx['totalBytes'], 'maxUtil', NNA), False), 
            fbps4('Utilized Line Rate (%s)',    get_param(resTx, 'lineRate', NNA, False),        get_param(resRx, 'lineRate', NNA, False), False),  
            fbps4('Information Rate (%s)',      get_param(resTx, 'dataRate', NNA, False),        get_param(resRx, 'dataRate', NNA, False), False), 
            
            ('Frame Size Under 64 Bytes',   get_param(resTx, 'fsz63', ICNA),  get_param(resRx, 'fsz63', ICNA), True), 
            ('Frame Size 64 Bytes',         get_param(resTx, 'fsz64', ICNA),  get_param(resRx, 'fsz64', ICNA), True), 
            ('Frame Size 65-127 Bytes',     get_param(resTx, 'fsz128', ICNA), get_param(resRx, 'fsz128', ICNA), True), 
            ('Frame Size 128-255 Bytes',    get_param(resTx, 'fsz256', ICNA), get_param(resRx, 'fsz256', ICNA), True), 
            ('Frame Size 256-511 Bytes',    get_param(resTx, 'fsz512', ICNA), get_param(resRx, 'fsz512', ICNA), True), 
            ('Frame Size 512-1023 Bytes',   get_param(resTx, 'fsz1024', ICNA),get_param(resRx, 'fsz1024', ICNA), True), 
            ('Frame Size 1024-1518 Bytes',  get_param(resTx, 'fsz1518', ICNA),get_param(resRx, 'fsz1518', ICNA), True), 
            ('Frame Size Over 1518 Bytes',  get_param(resTx, 'fsz1519', ICNA),get_param(resRx, 'fsz1519', ICNA), True)
        ]
        if self.test_mode in ('THROUGHPUT'):
            test_frames = \
            [
                ('Total Test Frames',           get_param(resTx['testFrames'], 'dummy'),      get_param(resRx['testFrames'], 'total', ICNA), True), 
                ('Frame Rate Current (fps)',    get_param(resTx['testFrames'], 'dummy'),      get_param(resRx['testFrames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['testFrames'], 'dummy'),      get_param(resRx['testFrames'], 'avgRate', NNA), False), 
                ('Total Non Test Frames',       get_param(resTx['nonTestFrames'], 'dummy'),   get_param(resRx['nonTestFrames'], 'total', ICNA), True), 
                ('Frame Rate Current (fps)',    get_param(resTx['nonTestFrames'], 'dummy'),   get_param(resRx['nonTestFrames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['nonTestFrames'], 'dummy'),   get_param(resRx['nonTestFrames'], 'avgRate', NNA), False)
            ]
            if test_layer == 'L2FRAME':
                nvp.extend(test_frames)    
        more_nvp = \
        [
                ('Total Unicast Frames',        get_param(resTx['uMacFrames'], 'total', ICNA),  get_param(resRx['uMacFrames'], 'total', ICNA), True), 
                ('Frame Rate Current (fps)',    get_param(resTx['uMacFrames'], 'curRate', NNA), get_param(resRx['uMacFrames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['uMacFrames'], 'avgRate', NNA), get_param(resRx['uMacFrames'], 'avgRate', NNA), False),                 
                ('Total Multicast Frames',      get_param(resTx['mMacFrames'], 'total', ICNA),  get_param(resRx['mMacFrames'], 'total', ICNA), True ), 
                ('Frame Rate Current (fps)',    get_param(resTx['mMacFrames'], 'curRate', NNA), get_param(resRx['mMacFrames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['mMacFrames'], 'avgRate', NNA), get_param(resRx['mMacFrames'], 'avgRate', NNA), False),                                 
                ('Total Broadcast Frames',      get_param(resTx['bMacFrames'], 'total', ICNA),  get_param(resRx['bMacFrames'], 'total', ICNA), True), 
                ('Frame Rate Current (fps)',    get_param(resTx['bMacFrames'], 'curRate', NNA), get_param(resRx['bMacFrames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['bMacFrames'], 'avgRate', NNA), get_param(resRx['bMacFrames'], 'avgRate', NNA), False),                 
                ('Total Keep Alive MAC Frames', get_param(resTx['kAliveMacFrames'], 'dummy'), get_param(resRx['kAliveMacFrames'], 'total', ICNA), True), 
                ('Frame Rate Current (fps)',    get_param(resTx['kAliveMacFrames'], 'dummy'), get_param(resRx['kAliveMacFrames'], 'curRate', NNA), False),  
                ('Frame Rate Average (fps)',    get_param(resTx['kAliveMacFrames'], 'dummy'), get_param(resRx['kAliveMacFrames'], 'avgRate', NNA), False),                 
                ('Total Invalid Frames',        get_param(resTx['invalidMacFrames'], 'dummy'), get_param(resRx['invalidMacFrames'], 'total', ICNA), True), 
                ('Frame Rate Current (fps)',    get_param(resTx['invalidMacFrames'], 'dummy'), get_param(resRx['invalidMacFrames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['invalidMacFrames'], 'dummy'), get_param(resRx['invalidMacFrames'], 'avgRate', NNA), False),                 
                ('Total VLAN Frames',           get_param(resTx['totalVlanFrames'], 'dummy'), get_param(resRx['totalVlanFrames'], 'total', ICNA), True ), 
                ('Frame Rate Current (fps)',    get_param(resTx['totalVlanFrames'], 'dummy'), get_param(resRx['totalVlanFrames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['totalVlanFrames'], 'dummy'), get_param(resRx['totalVlanFrames'], 'avgRate', NNA), False),
                ('Total Single-Tagged Frames',  get_param(resTx['sVlanFrames'], 'dummy'), get_param(resRx['sVlanFrames'], 'total', ICNA), True ),
                ('Frame Rate Current (fps)',    get_param(resTx['sVlanFrames'], 'dummy'), get_param(resRx['sVlanFrames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['sVlanFrames'], 'dummy'), get_param(resRx['sVlanFrames'], 'avgRate', NNA), False),
                ('Total Multi-Tagged Frames',   get_param(resTx['mVlanFrames'], 'dummy'), get_param(resRx['mVlanFrames'], 'total', ICNA), True),
                ('Frame Rate Current (fps)',    get_param(resTx['mVlanFrames'], 'dummy'), get_param(resRx['mVlanFrames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['mVlanFrames'], 'dummy'), get_param(resRx['mVlanFrames'], 'avgRate', NNA), False),
                ('Total MPLS Frames',           get_param(resTx['mplsFrames'], 'dummy'), get_param(resRx['mplsFrames'], 'total', ICNA), True),
                ('Frame Rate Current (fps)',    get_param(resTx['mplsFrames'], 'dummy'), get_param(resRx['mplsFrames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['mplsFrames'], 'dummy'), get_param(resRx['mplsFrames'], 'avgRate', NNA), False),
                ('Total IPv4 Frames',           get_param(resTx['ipv4Frames'], 'dummy'), get_param(resRx['ipv4Frames'], 'total', ICNA), True),
                ('Frame Rate Current (fps)',    get_param(resTx['ipv4Frames'], 'dummy'), get_param(resRx['ipv4Frames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['ipv4Frames'], 'dummy'), get_param(resRx['ipv4Frames'], 'avgRate', NNA), False),
                ('Total Unicast IPv4 Frames',   get_param(resTx['uIpv4Frames'], 'dummy'), get_param(resRx['uIpv4Frames'], 'total', ICNA), True),
                ('Frame Rate Current (fps)',    get_param(resTx['uIpv4Frames'], 'dummy'), get_param(resRx['uIpv4Frames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['uIpv4Frames'], 'dummy'), get_param(resRx['uIpv4Frames'], 'avgRate', NNA), False),                 
                ('Total Multicast IPv4 Frames', get_param(resTx['mIpv4Frames'], 'dummy'), get_param(resRx['mIpv4Frames'], 'total', ICNA), True),  
                ('Frame Rate Current (fps)',    get_param(resTx['mIpv4Frames'], 'dummy'), get_param(resRx['mIpv4Frames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['mIpv4Frames'], 'dummy'), get_param(resRx['mIpv4Frames'], 'avgRate', NNA), False),                 
                ('Total Broadcast IPv4 Frames', get_param(resTx['bIpv4Frames'], 'dummy'), get_param(resRx['bIpv4Frames'], 'total', ICNA), True),  
                ('Frame Rate Current (fps)',    get_param(resTx['bIpv4Frames'], 'dummy'), get_param(resRx['bIpv4Frames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['bIpv4Frames'], 'dummy'), get_param(resRx['bIpv4Frames'], 'avgRate', NNA), False),                 
        ]
        if self.test_mode != 'THROUGHPUT' or test_layer == 'L2FRAME':
            nvp.extend(more_nvp)
        if self.test_mode == 'MONITOR':
            IPv6 = \
            [
                ('Total IPv6 Frames',           get_param(resTx['ipv6Frames'], 'dummy'),  get_param(resRx['ipv6Frames'], 'total', ICNA), True),
                ('Frame Rate Current (fps)',    get_param(resTx['ipv6Frames'], 'dummy'),  get_param(resRx['ipv6Frames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['ipv6Frames'], 'dummy'),  get_param(resRx['ipv6Frames'], 'avgRate', NNA), False),
                ('Total Unicast IPv6 Frames',   get_param(resTx['uIpv6Frames'], 'dummy'), get_param(resRx['uIpv6Frames'], 'total', ICNA), True),
                ('Frame Rate Current (fps)',    get_param(resTx['uIpv6Frames'], 'dummy'), get_param(resRx['uIpv6Frames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['uIpv6Frames'], 'dummy'), get_param(resRx['uIpv6Frames'], 'avgRate', NNA), False),                 
                ('Total Multicast IPv6 Frames', get_param(resTx['mIpv6Frames'], 'dummy'), get_param(resRx['mIpv6Frames'], 'total', ICNA), True),  
                ('Frame Rate Current (fps)',    get_param(resTx['mIpv6Frames'], 'dummy'), get_param(resRx['mIpv6Frames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['mIpv6Frames'], 'dummy'), get_param(resRx['mIpv6Frames'], 'avgRate', NNA), False),                 
                ('Total Broadcast IPv6 Frames', get_param(resTx['bIpv6Frames'], 'dummy'), get_param(resRx['bIpv6Frames'], 'total', ICNA), True),  
                ('Frame Rate Current (fps)',    get_param(resTx['bIpv6Frames'], 'dummy'), get_param(resRx['bIpv6Frames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['bIpv6Frames'], 'dummy'), get_param(resRx['bIpv6Frames'], 'avgRate', NNA), False)                 
        
            ]
            nvp.extend(IPv6)
        if (self.test_mode == 'THROUGHPUT' and test_layer != 'L2FRAME') == False:
            tcp_udp_pause = \
            [
                ('Total TCP Frames',            get_param(resTx['tcpFrames'], 'dummy'),   get_param(resRx['tcpFrames'], 'total', ICNA), True), 
                ('Frame Rate Current (fps)',    get_param(resTx['tcpFrames'], 'dummy'),   get_param(resRx['tcpFrames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['tcpFrames'], 'dummy'),   get_param(resRx['tcpFrames'], 'avgRate', NNA), False), 
                
                ('Total UDP Frames',            get_param(resTx['udpFrames'], 'dummy'),   get_param(resRx['udpFrames'], 'total', ICNA), True), 
                ('Frame Rate Current (fps)',    get_param(resTx['udpFrames'], 'dummy'),   get_param(resRx['udpFrames'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(resTx['udpFrames'], 'dummy'),   get_param(resRx['udpFrames'], 'avgRate', NNA), False), 
                ('Total Pause Frames',          get_param(resTx['pauseFrames'], 'total', ICNA),   get_param(resRx['pauseFrames'], 'total', ICNA), True),
            ]
            nvp.extend(tcp_udp_pause)
        #if self.test_mode == 'RFC2544':
        #    results = params['result_rfc2544']['result'];
        #    lbResTx = results['txStats'];
        #    lbResRx = results['rxStats'];
        #    jitter_nvp = \
        #    [
        #        ('Frame Delay Variation Minimum',   get_param(lbResTx['packetJitter'], 'dummy'),  get_param(lbResRx['packetJitter'], 'min', NNA), True),
        #        ('Frame Delay Variation Maximum',   get_param(lbResTx['packetJitter'], 'dummy'),    get_param(lbResRx['packetJitter'], 'max', NNA), True),
        #        ('Frame Delay Variation Average',   get_param(lbResTx['packetJitter'], 'dummy'),    get_param(lbResRx['packetJitter'], 'avg', NNA), True)
        #    ]
        #    nvp.extend(jitter_nvp)
       
        #if self.test_mode in ('THROUGHPUT'):
        #    frGap_SrvDis_Lat = \
        #    [
        #        ('Frame Gap Minimum',               get_param(lbResTx['frameGap'], 'min'),        get_param(lbResRx['frameGap'], 'min'), True),
        #        ('Frame Gap Maximum',               get_param(lbResTx['frameGap'], 'max'),        get_param(lbResRx['frameGap'], 'max'), True),
        #        ('Frame Gap Average',               get_param(lbResTx['frameGap'], 'avg'),        get_param(lbResRx['frameGap'], 'avg'), True),
        #        ('Service Disruption Events',       get_param(lbResTx['servDisrupt'], 'events'),   get_param(lbResRx['servDisrupt'], 'events'), True),
        #        ('Service Disruption Duration',     get_param(lbResTx['servDisrupt'], 'duration'),   get_param(lbResRx['servDisrupt'], 'duration'), True),
        #        ('Service Disruption Minimum',      get_param(lbResTx['servDisrupt'], 'min'),   get_param(lbResRx['servDisrupt'], 'min'), True),
        #        ('Service Disruption Maximum',      get_param(lbResTx['servDisrupt'], 'max'),   get_param(lbResRx['servDisrupt'], 'max'), True),
        #        ('Service Disruption Average',      get_param(lbResTx['servDisrupt'], 'avg'),   get_param(lbResRx['servDisrupt'], 'avg'), True),
        #        ('Latency Previous',                get_param(lbResTx['latency'], 'previous'),         get_param(lbResRx['latency'], 'previous'), True),
        #        ('Latency Current',                 get_param(lbResTx['latency'], 'current'),          get_param(lbResRx['latency'], 'current'), True),
        #        ('Latency Total',                   get_param(lbResTx['latency'], 'total'),          get_param(lbResRx['latency'], 'total'), True)
        #    ]
        #    nvp.extend(frGap_SrvDis_Lat)

        #if self.test_mode in ('LOOPBACK', 'IP'):
        #    results = params['result'][0]['eth']
        #    lbResTx = results['txStats'];
        #    lbResRx = results['rxStats'];
        #    frGap_SrvDis_Lat = \
        #    [
        #        ('Frame Delay Variation Minimum',   get_param(lbResTx['packetJitter'], 'dummy'),    get_param(lbResRx['packetJitter'], 'min', NNA), True),
        #        ('Frame Delay Variation Maximum',   get_param(lbResTx['packetJitter'], 'dummy'),    get_param(lbResRx['packetJitter'], 'max', NNA), True),
        #        ('Frame Delay Variation Average',   get_param(lbResTx['packetJitter'], 'dummy'),    get_param(lbResRx['packetJitter'], 'avg', NNA), True),
        #        ('Frame Gap Minimum',               get_param(lbResTx['frameGap'], 'dummy'),   '', True),     #get_param(lbResRx['frameGap'], 'min'), True),
        #        ('Frame Gap Maximum',               get_param(lbResTx['frameGap'], 'dummy'),   '', True),     #get_param(lbResRx['frameGap'], 'max'), True),
        #        ('Frame Gap Average',               get_param(lbResTx['frameGap'], 'dummy'),   '', True),     #get_param(lbResRx['frameGap'], 'avg'), True),
        #        ('Service Disruption Events',       get_param(lbResTx['servDisrupt'], 'dummy'),'', True),   #get_param(lbResRx['servDisrupt'], 'events'), True),
        #        ('Service Disruption Duration',     get_param(lbResTx['servDisrupt'], 'dummy'),'', True),   #get_param(lbResRx['servDisrupt'], 'duration'), True),
        #        ('Service Disruption Minimum',      get_param(lbResTx['servDisrupt'], 'dummy'),'', True),   #get_param(lbResRx['servDisrupt'], 'min'), True),
        #        ('Service Disruption Maximum',      get_param(lbResTx['servDisrupt'], 'dummy'),'', True),   #get_param(lbResRx['servDisrupt'], 'max'), True),
        #        ('Service Disruption Average',      get_param(lbResTx['servDisrupt'], 'dummy'),'', True),   #get_param(lbResRx['servDisrupt'], 'avg'), True),
        #        ('Latency Minimum',                 get_param(lbResTx['latency'], 'dummy'),    '', True),     #get_param(lbResRx['latency'], 'min'), True),
        #        ('Latency Maximum',                 get_param(lbResTx['latency'], 'dummy'),    '', True),      #get_param(lbResRx['latency'], 'max'), True),
        #        ('Latency Average',                 get_param(lbResTx['latency'], 'dummy'),    '', True),      #get_param(lbResRx['latency'], 'avg'), True)
        #    ]
        #    nvp.extend(frGap_SrvDis_Lat)
        if self.test_mode in ('THROUGHPUT', 'MONITOR'):
            losevent = \
            [
                        ('LOS Event',               get_param(errTx['los'], 'dummy'),                get_param(errRx['los'], 'total', ICNA), True), 
                        ('LOSS Aggregate (secs)',   get_param(errTx['los'], 'dummy'),                get_param(errRx['los'], 'time', NNA), True), 
                        ('LOSS Minimum (secs)',     get_param(errTx['los'], 'dummy'),                get_param(errRx['los'], 'min', NNA), True), 
                        ('LOSS Maximum (secs)',     get_param(errTx['los'], 'dummy'),                get_param(errRx['los'], 'max', NNA), True), 
                        ('LOSS Current (secs)',     get_param(errTx['los'], 'dummy'),                get_param(errRx['los'], 'cur', NNA), True), 
                        ('LOSS Average (secs)',     get_param(errTx['los'], 'dummy'),                get_param(errRx['los'], 'avg', NNA), True),
                        ('LOSync Event',            get_param(errTx['losync'], 'dummy'),             get_param(errRx['losync'], 'total', ICNA), True), 
                        ('LOSync Aggregate (secs)', get_param(errTx['losync'], 'dummy'),             get_param(errRx['losync'], 'time', NNA), True), 
                        ('LOSync Minimum (secs)',   get_param(errTx['losync'], 'dummy'),             get_param(errRx['losync'], 'min', NNA), True), 
                        ('LOSync Maximum (secs)',   get_param(errTx['losync'], 'dummy'),             get_param(errRx['losync'], 'max', NNA), True), 
                        ('LOSync Current (secs)',   get_param(errTx['losync'], 'dummy'),             get_param(errRx['losync'], 'cur', NNA), True), 
                        ('LOSync Average (secs)',   get_param(errTx['losync'], 'dummy'),             get_param(errRx['losync'], 'avg', NNA), True)
            ]
            nvp.extend(losevent)
        if self.test_mode in ('THROUGHPUT', 'RFC2544', 'MONITOR', 'LOOPBACK'):
            Total_FCS = \
            [
                        ('Total FCS/CRC Error',      get_param(errTx['fcsError'], 'total', ICNA),   get_param(errRx['fcsError'], 'total', ICNA), True), 
                        ('Frame Rate Current (fps)', get_param(errTx['fcsError'], 'curRate', NNA),  get_param(errRx['fcsError'], 'curRate', NNA), False), 
                        ('Frame Rate Average (fps)', get_param(errTx['fcsError'], 'avgRate', NNA),  get_param(errRx['fcsError'], 'avgRate', NNA), False)
            ]
            nvp.extend(Total_FCS)
        if self.test_mode in ('THROUGHPUT'):
            checksum_errors = \
            [ 
                ('Total IP Checksum Error',  get_param(errTx['ipChecksumError'], 'dummy'),    get_param(errRx['ipChecksumError'], 'total', ICNA), True),
                ('Frame Rate Current (fps)', get_param(errTx['ipChecksumError'], 'dummy'),    get_param(errRx['ipChecksumError'], 'curRate'), False),  
                ('Frame Rate Average (fps)', get_param(errTx['ipChecksumError'], 'dummy'),    get_param(errRx['ipChecksumError'], 'avgRate'), False), 
                ('Total TCP Checksum Error', get_param(errTx['tcpChecksumError'], 'dummy'),   get_param(errRx['tcpChecksumError'], 'total', ICNA), True), 
                ('Frame Rate Current (fps)', get_param(errTx['tcpChecksumError'], 'dummy'),   get_param(errRx['tcpChecksumError'], 'curRate'), False), 
                ('Frame Rate Average (fps)', get_param(errTx['tcpChecksumError'], 'dummy'),   get_param(errRx['tcpChecksumError'], 'avgRate'), False),
                ('Total UDP Checksum Error', get_param(errTx['udpChecksumError'], 'dummy'),   get_param(errRx['udpChecksumError'], 'total', ICNA), True), 
                ('Frame Rate Current (fps)', get_param(errTx['udpChecksumError'], 'dummy'),   get_param(errRx['udpChecksumError'], 'curRate'), False), 
                ('Frame Rate Average (fps)', get_param(errTx['udpChecksumError'], 'dummy'),   get_param(errRx['udpChecksumError'], 'avgRate'), False), 
            ]
            if test_layer == 'L2FRAME':
                nvp.extend(checksum_errors)
        
        if self.test_mode in ('THROUGHPUT'):
            sequence_errors = \
            [                    
                #('Lost SN Error',               get_param(errTx['lostSnError'], 'total'),       get_param(errRx['lostSnError'], 'total'), False), 
                ('Total Frame Loss Ratio',      get_param(errTx['lostSnError'], 'dummy'),       get_param(errRx['lostSnError'], 'total', ICNA), True), 
                ('Frame Rate Current (fps)',    get_param(errTx['lostSnError'], 'dummy'),       get_param(errRx['lostSnError'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(errTx['lostSnError'], 'dummy'),       get_param(errRx['lostSnError'], 'avgRate', NNA), False),            
                ('Total Out of Sequence Error', get_param(errTx['outOfSeqError'], 'dummy'),     get_param(errRx['outOfSeqError'], 'total', ICNA), True), 
                ('Frame Rate Current (fps)',    get_param(errTx['outOfSeqError'], 'dummy'),     get_param(errRx['outOfSeqError'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(errTx['outOfSeqError'], 'dummy'),     get_param(errRx['outOfSeqError'], 'avgRate', NNA), False),                 
                ('Total Duplicate SN Error',    get_param(errTx['dupSnError'], 'dummy'),        get_param(errRx['dupSnError'], 'total', ICNA), True), 
                ('Frame Rate Current (fps)',    get_param(errTx['dupSnError'], 'dummy'),        get_param(errRx['dupSnError'], 'curRate', NNA), False), 
                ('Frame Rate Average (fps)',    get_param(errTx['dupSnError'], 'dummy'),        get_param(errRx['dupSnError'], 'avgRate', NNA), False)
            ]
            bit_errors = \
            [                    
                ('Bit Error',                   get_param(errTx['bitError'], 'total', ICNA),        get_param(errRx['bitError'], 'total', ICNA), True), 
                ('Current Bit',                 get_param(errTx['bitError'], 'current', ICNA),      get_param(errRx['bitError'], 'current', ICNA), False), 
                ('Current Bit Error Rate',      get_param(errTx['bitError'], 'curBitRate', EXP),    get_param(errRx['bitError'], 'curBitRate', EXP), False),
                ('Bit Error Rate',              get_param(errTx['bitError'], 'bitRate', EXP),       get_param(errRx['bitError'], 'bitRate', EXP), False), 
                ('LOPS (secs)',                 get_param(errTx['bitError'], 'lopsTime', NNA),      get_param(errRx['bitError'], 'lopsTime', NNA), False), 
                ('No BERT Traffic (secs)',      get_param(errTx['bitError'], 'noBertTraffic', NNA), get_param(errRx['bitError'], 'noBertTraffic', NNA), False)
            ]
            if test_layer == 'L2FRAME':
                nvp.extend(sequence_errors)   
            else:
                nvp.extend(bit_errors)   
        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable                                    
            #if self.test_mode == 'MONITOR':
             #   table.append(['',primaryPortID+' Receive',secondaryPortID+' Receive'])
              #  for n,tx_v,rx_v,p in nvp:
               #     table.append([
                #                    n,
                 #                   get_param(primary_result, rx_v, NA, p),
                  #                  get_param(secondary_result, rx_v, NA, p)
                   #             ])            
            #else:
            if self.test_mode == 'MONITOR' and self.primaryPortID != self.secondaryPortID:
                table.append(['Statistic Description', self.primaryPortID, self.secondaryPortID])
            else :
                table.append(['Statistic Description', 'Transmitted', 'Received'])
            for n, tx_v, rx_v, bolt in nvp:
                if bolt:
                    n = Paragraph('<b>%s</b>' % n, styles["Normal"])
                table.append([n, tx_v, rx_v])
        else:       
            makeTable = self.createCsvTable

            #if self.test_mode == 'MONITOR':
             #   table.append(['',primaryPortID+' Receive',secondaryPortID+' Receive'])
              #  for n,tx_v,rx_v,p in nvp:
               #     table.append([
                #                    n,
                 #                   get_param(primary_result, rx_v, NA, p),
                  #                  get_param(secondary_result, rx_v, NA, p)
                   #             ])            
            #else:
            if self.test_mode == 'MONITOR' and self.primaryPortID != self.secondaryPortID:
                table.append(['Statistic Description', self.primaryPortID, self.secondaryPortID])
            else :
                table.append(['Statistic Description', 'Transmitted', 'Received'])
            for n, tx_v, rx_v, unused in nvp:
                table.append([n, tx_v, rx_v])
            
        makeTable(fd,"Aggregate Data",table)

    def MonitoraggregateTable(self, fd, params, format):
        """Writes Aggregate Result Table
           @type  fd: Report File Object
           @param fd: Descriptor to current report object
           @param params: Table data
           @type  format: String 
           @param format: 'pdf' or 'csv'
        """
        #self.write_log('MonitoraggregateTable Start')
        
        try:
            if self.primaryPortID == self.secondaryPortID:
                primary = params['result_monitor']['primary']
                secondary = primary
            else:
                primary = params['result_monitor']['primary']
                secondary = params['result_monitor']['secondary']
        except:
            self.write_log('MONITOR setup data not found!', 'Error', sys.exc_info())
            return
        
        try:
            statsP = primary['rxStats']
            statsS = secondary['rxStats']
        except:
            self.write_log('No Aggregate Stats Data', 'Error', sys.exc_info())
            statsP = {}
            statsS = {}
        
        try:
            errP = primary['rxError']
            errS = secondary['rxError']
        except:
            self.write_log('No Aggregate Error Data', 'Error', sys.exc_info())
            errP = {}
            errS = {}

        # ( Description, Tx Param Name, Rx Param Name )
        nvp = \
        [
            ('Total Frames',                    get_param(statsP['totalFrames'], 'total', ICNA),   get_param(statsS['totalFrames'], 'total', ICNA), True), 
            ('Total Bytes',                     get_param(statsP['totalBytes'], 'total', ICNA),    get_param(statsS['totalBytes'], 'total', ICNA), True), 
            ('Frame Rate Current (fps)',        get_param(statsP['totalFrames'], 'curRate', CNA), get_param(statsS['totalFrames'], 'curRate', CNA), False), 
            ('Frame Rate Average (fps)',        get_param(statsP['totalFrames'], 'avgRate', CNA), get_param(statsS['totalFrames'], 'avgRate', CNA), False),  
            ('Frame Rate Minimum (fps)',        get_param(statsP['totalFrames'], 'minRate', CNA), get_param(statsS['totalFrames'], 'minRate', CNA), False),  
            ('Frame Rate Maximum (fps)',        get_param(statsP['totalFrames'], 'maxRate', CNA), get_param(statsS['totalFrames'], 'maxRate', CNA), False), 
            ('Utilized Line Rate Current (%)',  get_param(statsP['totalBytes'], 'curUtil', NNA),  get_param(statsS['totalBytes'], 'curUtil', NNA), False), 
            ('Utilized Line Rate Average (%)',  get_param(statsP['totalBytes'], 'avgUtil', NNA),  get_param(statsS['totalBytes'], 'avgUtil', NNA), False), 
            ('Utilized Line Rate Minimum (%)',  get_param(statsP['totalBytes'], 'minUtil', NNA),  get_param(statsS['totalBytes'], 'minUtil', NNA), False), 
            ('Utilized Line Rate Maximum (%)',  get_param(statsP['totalBytes'], 'maxUtil', NNA),  get_param(statsS['totalBytes'], 'maxUtil', NNA), False), 
            fbps4('Utilized Line Rate (%s)',    get_param(statsP, 'lineRate', NNA, False),        get_param(statsS, 'lineRate', NNA, False), False),  
            fbps4('Information Rate (%s)',      get_param(statsP, 'dataRate', NNA, False),        get_param(statsS, 'dataRate', NNA, False), False), 
            
            ('Frame Size Under 64 Bytes',   get_param(statsP, 'fsz63', ICNA),  get_param(statsS, 'fsz63', ICNA), True), 
            ('Frame Size 64 Bytes',         get_param(statsP, 'fsz64', ICNA),  get_param(statsS, 'fsz64', ICNA), True), 
            ('Frame Size 65-127 Bytes',     get_param(statsP, 'fsz128', ICNA), get_param(statsS, 'fsz128', ICNA), True), 
            ('Frame Size 128-255 Bytes',    get_param(statsP, 'fsz256', ICNA), get_param(statsS, 'fsz256', ICNA), True), 
            ('Frame Size 256-511 Bytes',    get_param(statsP, 'fsz512', ICNA), get_param(statsS, 'fsz512', ICNA), True), 
            ('Frame Size 512-1023 Bytes',   get_param(statsP, 'fsz1024', ICNA),get_param(statsS, 'fsz1024', ICNA), True), 
            ('Frame Size 1024-1518 Bytes',  get_param(statsP, 'fsz1518', ICNA),get_param(statsS, 'fsz1518', ICNA), True), 
            ('Frame Size Over 1518 Bytes',  get_param(statsP, 'fsz1519', ICNA),get_param(statsS, 'fsz1519', ICNA), True)
        ]
        nvp.extend(nvp)

        more_nvp = \
        [
            ('Total Unicast Frames',        get_param(statsP['uMacFrames'], 'total', ICNA),  get_param(statsS['uMacFrames'], 'total', ICNA), True), 
            ('Frame Rate Current (fps)',    get_param(statsP['uMacFrames'], 'curRate', NNA), get_param(statsS['uMacFrames'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)',    get_param(statsP['uMacFrames'], 'avgRate', NNA), get_param(statsS['uMacFrames'], 'avgRate', NNA), False),                 
            ('Total Multicast Frames',      get_param(statsP['mMacFrames'], 'total', ICNA),  get_param(statsS['mMacFrames'], 'total', ICNA), True ), 
            ('Frame Rate Current (fps)',    get_param(statsP['mMacFrames'], 'curRate', NNA), get_param(statsS['mMacFrames'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)',    get_param(statsP['mMacFrames'], 'avgRate', NNA), get_param(statsS['mMacFrames'], 'avgRate', NNA), False),                                 
            ('Total Broadcast Frames',      get_param(statsP['bMacFrames'], 'total', ICNA),  get_param(statsS['bMacFrames'], 'total', ICNA), True), 
            ('Frame Rate Current (fps)',    get_param(statsP['bMacFrames'], 'curRate', NNA), get_param(statsS['bMacFrames'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)',    get_param(statsP['bMacFrames'], 'avgRate', NNA), get_param(statsS['bMacFrames'], 'avgRate', NNA), False),                 
            ('Total Keep Alive MAC Frames', get_param(statsP['kAliveMacFrames'], 'total', ICNA),   get_param(statsS['kAliveMacFrames'], 'total', ICNA), True), 
            ('Frame Rate Current (fps)',    get_param(statsP['kAliveMacFrames'], 'curRate', NNA), get_param(statsS['kAliveMacFrames'], 'curRate', NNA), False),  
            ('Frame Rate Average (fps)',    get_param(statsP['kAliveMacFrames'], 'avgRate', NNA), get_param(statsS['kAliveMacFrames'], 'avgRate', NNA), False),                 
            ('Total Invalid Frames',        get_param(statsP['invalidMacFrames'], 'total', ICNA),  get_param(statsS['invalidMacFrames'], 'total', ICNA), True), 
            ('Frame Rate Current (fps)',    get_param(statsP['invalidMacFrames'], 'curRate', NNA), get_param(statsS['invalidMacFrames'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)',    get_param(statsP['invalidMacFrames'], 'avgRate', NNA), get_param(statsS['invalidMacFrames'], 'avgRate', NNA), False),                 
            ('Total VLAN Frames',           get_param(statsP['totalVlanFrames'], 'total', ICNA),   get_param(statsS['totalVlanFrames'], 'total', ICNA), True ), 
            ('Frame Rate Current (fps)',    get_param(statsP['totalVlanFrames'], 'curRate', NNA), get_param(statsS['totalVlanFrames'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)',    get_param(statsP['totalVlanFrames'], 'avgRate', NNA), get_param(statsS['totalVlanFrames'], 'avgRate', NNA), False),
            ('Total Single-Tagged Frames',  get_param(statsP['sVlanFrames'], 'total', ICNA),  get_param(statsS['sVlanFrames'], 'total', ICNA), True ),
            ('Frame Rate Current (fps)',    get_param(statsP['sVlanFrames'], 'curRate', NNA), get_param(statsS['sVlanFrames'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)',    get_param(statsP['sVlanFrames'], 'avgRate', NNA), get_param(statsS['sVlanFrames'], 'avgRate', NNA), False),
            ('Total Multi-Tagged Frames',   get_param(statsP['mVlanFrames'], 'total', ICNA),  get_param(statsS['mVlanFrames'], 'total', ICNA), True),
            ('Frame Rate Current (fps)',    get_param(statsP['mVlanFrames'], 'curRate', NNA), get_param(statsS['mVlanFrames'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)',    get_param(statsP['mVlanFrames'], 'avgRate', NNA), get_param(statsS['mVlanFrames'], 'avgRate', NNA), False),
            ('Total MPLS Frames',           get_param(statsP['mplsFrames'], 'total', ICNA),   get_param(statsS['mplsFrames'], 'total', ICNA), True),
            ('Frame Rate Current (fps)',    get_param(statsP['mplsFrames'], 'curRate', NNA),  get_param(statsS['mplsFrames'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)',    get_param(statsP['mplsFrames'], 'avgRate', NNA),  get_param(statsS['mplsFrames'], 'avgRate', NNA), False),
            ('Total IPv4 Frames',           get_param(statsP['ipv4Frames'], 'total', ICNA),   get_param(statsS['ipv4Frames'], 'total', ICNA), True),
            ('Frame Rate Current (fps)',    get_param(statsP['ipv4Frames'], 'curRate', NNA),  get_param(statsS['ipv4Frames'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)',    get_param(statsP['ipv4Frames'], 'avgRate', NNA),  get_param(statsS['ipv4Frames'], 'avgRate', NNA), False),
            ('Total Unicast IPv4 Frames',   get_param(statsP['uIpv4Frames'], 'total', ICNA),  get_param(statsS['uIpv4Frames'], 'total', ICNA), True),
            ('Frame Rate Current (fps)',    get_param(statsP['uIpv4Frames'], 'curRate', NNA), get_param(statsS['uIpv4Frames'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)',    get_param(statsP['uIpv4Frames'], 'avgRate', NNA), get_param(statsS['uIpv4Frames'], 'avgRate', NNA), False),                 
            ('Total Multicast IPv4 Frames', get_param(statsP['mIpv4Frames'], 'total', ICNA),  get_param(statsS['mIpv4Frames'], 'total', ICNA), True),  
            ('Frame Rate Current (fps)',    get_param(statsP['mIpv4Frames'], 'curRate', NNA), get_param(statsS['mIpv4Frames'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)',    get_param(statsP['mIpv4Frames'], 'avgRate', NNA), get_param(statsS['mIpv4Frames'], 'avgRate', NNA), False),                 
            ('Total Broadcast IPv4 Frames', get_param(statsP['bIpv4Frames'], 'total', ICNA),  get_param(statsS['bIpv4Frames'], 'total', ICNA), True),  
            ('Frame Rate Current (fps)',    get_param(statsP['bIpv4Frames'], 'curRate', NNA), get_param(statsS['bIpv4Frames'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)',    get_param(statsP['bIpv4Frames'], 'avgRate', NNA), get_param(statsS['bIpv4Frames'], 'avgRate', NNA), False),                 
        ]
        nvp.extend(more_nvp)

        IPv6 = \
        [
            ('Total IPv6 Frames',           get_param(statsP['ipv6Frames'], 'total', ICNA),   get_param(statsS['ipv6Frames'], 'total', ICNA), True),
            ('Frame Rate Current (fps)',    get_param(statsP['ipv6Frames'], 'curRate', NNA),  get_param(statsS['ipv6Frames'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)',    get_param(statsP['ipv6Frames'], 'avgRate', NNA),  get_param(statsS['ipv6Frames'], 'avgRate', NNA), False),
            ('Total Unicast IPv6 Frames',   get_param(statsP['uIpv6Frames'], 'total', ICNA),  get_param(statsS['uIpv6Frames'], 'total', ICNA), True),
            ('Frame Rate Current (fps)',    get_param(statsP['uIpv6Frames'], 'curRate', NNA), get_param(statsS['uIpv6Frames'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)',    get_param(statsP['uIpv6Frames'], 'avgRate', NNA), get_param(statsS['uIpv6Frames'], 'avgRate', NNA), False),                 
            ('Total Multicast IPv6 Frames', get_param(statsP['mIpv6Frames'], 'total', ICNA),  get_param(statsS['mIpv6Frames'], 'total', ICNA), True),  
            ('Frame Rate Current (fps)',    get_param(statsP['mIpv6Frames'], 'curRate', NNA), get_param(statsS['mIpv6Frames'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)',    get_param(statsP['mIpv6Frames'], 'avgRate', NNA), get_param(statsS['mIpv6Frames'], 'avgRate', NNA), False),                 
            ('Total Broadcast IPv6 Frames', get_param(statsP['bIpv6Frames'], 'total', ICNA),  get_param(statsS['bIpv6Frames'], 'total', ICNA), True),  
            ('Frame Rate Current (fps)',    get_param(statsP['bIpv6Frames'], 'curRate', NNA), get_param(statsS['bIpv6Frames'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)',    get_param(statsP['bIpv6Frames'], 'avgRate', NNA), get_param(statsS['bIpv6Frames'], 'avgRate', NNA), False)                 
        
        ]
        nvp.extend(IPv6)
       
        losevent = \
        [
            ('LOS Event',               get_param(errP['los'], 'total', ICNA),             get_param(errS['los'], 'total', ICNA), True), 
            ('LOSS Aggregate (secs)',   get_param(errP['los'], 'time', NNA),               get_param(errS['los'], 'time', NNA), True), 
            ('LOSS Minimum (secs)',     get_param(errP['los'], 'min', NNA),                get_param(errS['los'], 'min', NNA), True), 
            ('LOSS Maximum (secs)',     get_param(errP['los'], 'max', NNA),                get_param(errS['los'], 'max', NNA), True), 
            ('LOSS Current (secs)',     get_param(errP['los'], 'cur', NNA),                get_param(errS['los'], 'cur', NNA), True), 
            ('LOSS Average (secs)',     get_param(errP['los'], 'avg', NNA),                get_param(errS['los'], 'avg', NNA), True),
            ('LOSync Event',            get_param(errP['losync'], 'total', ICNA),          get_param(errS['losync'], 'total', ICNA), True), 
            ('LOSync Aggregate (secs)', get_param(errP['losync'], 'time', NNA),            get_param(errS['losync'], 'time', NNA), True), 
            ('LOSync Minimum (secs)',   get_param(errP['losync'], 'min', NNA),             get_param(errS['losync'], 'min', NNA), True), 
            ('LOSync Maximum (secs)',   get_param(errP['losync'], 'max', NNA),             get_param(errS['losync'], 'max', NNA), True), 
            ('LOSync Current (secs)',   get_param(errP['losync'], 'cur', NNA),             get_param(errS['losync'], 'cur', NNA), True), 
            ('LOSync Average (secs)',   get_param(errP['losync'], 'avg', NNA),             get_param(errS['losync'], 'avg', NNA), True)
        ]
        nvp.extend(losevent)
        
        Total_FCS = \
        [
            ('Total FCS/CRC Error',      get_param(errP['fcsError'], 'total', ICNA),   get_param(errS['fcsError'], 'total', ICNA), True), 
            ('Frame Rate Current (fps)', get_param(errP['fcsError'], 'curRate', NNA),  get_param(errS['fcsError'], 'curRate', NNA), False), 
            ('Frame Rate Average (fps)', get_param(errP['fcsError'], 'avgRate', NNA),  get_param(errS['fcsError'], 'avgRate', NNA), False)
        ]
        nvp.extend(Total_FCS)

        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable                                    
            if self.primaryPortID != self.secondaryPortID:
                table.append(['Statistic Description', '%s Received'%self.primaryPortID, '%s Received'%self.secondaryPortID])
            else :
                table.append(['Statistic Description', 'Received'])
                
            for n, p_v, s_v, bolt in nvp:
                if bolt:
                    n = Paragraph('<b>%s</b>' % n, styles["Normal"])
                if self.primaryPortID != self.secondaryPortID:
                    table.append([n, p_v, s_v])
                else :
                    table.append([n, p_v])
                    
        else:       
            makeTable = self.createCsvTable

            if self.primaryPortID != self.secondaryPortID:
                table.append(['Statistic Description', '%s Received'%self.primaryPortID, '%s Received'%self.secondaryPortID])
            else :
                table.append(['Statistic Description', 'Received'])
                
            for n, p_v, s_v, unused in nvp:
                if self.primaryPortID != self.secondaryPortID:
                    table.append([n, p_v, s_v])
                else :
                    table.append([n, p_v])
                
        makeTable(fd,"Aggregate Data",table)

    def aggregateTableFC_FC1(self, fd, params, format):
        """Writes Aggregate Result Table
           @type  fd: Report File Object
           @param fd: Descriptor to current report object
           @type  primary_result: Dictionary 
           @param primary_result: Main Port Results
           @type  secondary_result: Dictionary 
           @param secondary_result: Seconday Port Results           
           @type  ports: Dictionary 
           @param ports: Port Configuration
           @type  format: String 
           @param format: 'pdf' or 'csv'
        """

        if self.test_mode == 'FC_BERT':
            results = params['result_fc_bert']['result']
            resTx = results['tx']['txFrameStats']
            resRx = results['rx']['rxFrameStats']
            errTx = results['tx']['txErr']
            errRx = results['rx']['rxErr']

        # ( Description, Tx Param Name, Rx Param Name )
        nvp = \
        [
            ('Utilized Line Rate (kbps)',        get_param(resTx, 'lineRate', ICNA),               get_param(resRx, 'lineRate', ICNA), True),  
            ('Bit Error',                        get_param(errTx['baseErr']['bitError'], 'total', ICNA),    get_param(errRx['baseErr']['bitError'], 'total', ICNA), True), 
            ('Symbol Error',                     get_param(errTx['baseErr'], 'symbol', ICNA),    get_param(errRx['baseErr'], 'symbol', ICNA), True),
            ('Disparity Error',                  get_param(errTx['baseErr'], 'disparity', ICNA),    get_param(errRx['baseErr'], 'disparity', ICNA), True), 
            ('LOS (Loss Of Signal)',             NA,    get_param(errRx['los'], 'total', ICNA), True), 
            ('LOS Seconds (secs)',               NA,    get_param(errRx['los'], 'time', FNA), True),
            ('LOSYNC (Loss Of Sync)',            NA,    get_param(errRx['losync'], 'total', ICNA), True),
            ('LOSYNC Seconds (secs)',            NA,    get_param(errRx['losync'], 'time', FNA), True),
        ]

        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable                                    

            table.append(['Statistic Description', 'Transmitted', 'Received'])
            for n, tx_v, rx_v, bolt in nvp:
                if bolt:
                    n = Paragraph('<b>%s</b>' % n, styles["Normal"])
                table.append([n, tx_v, rx_v])
        else:       
            makeTable = self.createCsvTable

            table.append(['Statistic Description', 'Transmitted', 'Received'])
            for n, tx_v, rx_v, unused in nvp:
                table.append([n, tx_v, rx_v])
            
        makeTable(fd,"Aggregate Data",table)

        
    def aggregateTableFC(self, fd, params, format):
        """
           Writes Aggregate Result Table
           @type  fd: Report File Object
           @param fd: Descriptor to current report object
           @type  primary_result: Dictionary 
           @param primary_result: Main Port Results
           @type  secondary_result: Dictionary 
           @param secondary_result: Seconday Port Results           
           @type  ports: Dictionary 
           @param ports: Port Configuration
           @type  format: String 
           @param format: 'pdf' or 'csv'
        """

        if self.test_mode == 'FC_BERT':
            results = params['result_fc_bert']['result']
            resTx = results['tx']['txFrameStats']
            resRx = results['rx']['rxFrameStats']
            errTx = results['tx']['txErr']
            errRx = results['rx']['rxErr']
        elif self.test_mode == 'FC_LOOPBACK':
            results = params['result_fc_loopback']['result']
            resTx = results['txStats']
            resRx = results['rxStats']
            errTx = results['txError']
            errRx = results['rxError']
        elif self.test_mode == 'FC_RFC2544':
            results = params['result_fc_rfc2544']['result']
            resTx = results['txStats']
            resRx = results['rxStats']
            errTx = results['txError']
            errRx = results['rxError']

        # ( Description, Tx Param Name, Rx Param Name )
        nvp = \
        [
            ('Total Frames',                    get_param(resTx['totalFrames'], 'total', ICNA),   get_param(resRx['totalFrames'], 'total', ICNA), True), 
            ('Total Bytes',                     get_param(resTx['totalBytes'], 'total', ICNA),    get_param(resRx['totalBytes'], 'total', ICNA), True), 
            ('Frame Rate Current (fps)',        get_param(resTx['totalFrames'], 'curRate', FNA), get_param(resRx['totalFrames'], 'curRate', FNA), False), 
            ('Frame Rate Average (fps)',        get_param(resTx['totalFrames'], 'avgRate', FNA), get_param(resRx['totalFrames'], 'avgRate', FNA), False),  
            ('Frame Rate Minimum (fps)',        get_param(resTx['totalFrames'], 'minRate', FNA), get_param(resRx['totalFrames'], 'minRate', FNA), False),  
            ('Frame Rate Maximum (fps)',        get_param(resTx['totalFrames'], 'maxRate', FNA), get_param(resRx['totalFrames'], 'maxRate', FNA), False), 
            ('Utilized Line Rate Current (%)',  get_param(resTx['totalBytes'], 'curUtil', FNA),  get_param(resRx['totalBytes'], 'curUtil', FNA), False), 
            ('Utilized Line Rate Average (%)',  get_param(resTx['totalBytes'], 'avgUtil', FNA),  get_param(resRx['totalBytes'], 'avgUtil', FNA), False), 
            ('Utilized Line Rate Minimum (%)',  get_param(resTx['totalBytes'], 'minUtil', FNA),  get_param(resRx['totalBytes'], 'minUtil', FNA), False), 
            ('Utilized Line Rate Maximum (%)',  get_param(resTx['totalBytes'], 'maxUtil', FNA),  get_param(resRx['totalBytes'], 'maxUtil', FNA), False), 
            ('Utilized Line Rate (kbps)',       get_param(resTx, 'lineRate', ICNA),               get_param(resRx, 'lineRate', ICNA), False),  
            ('Information Rate (kbps)',         get_param(resTx, 'dataRate', ICNA),               get_param(resRx, 'dataRate', ICNA), False), 
        ]

        if self.test_mode != 'FC_LOOPBACK':
            interFrameDelay = \
            [
                ('Inter-Frame Delay,Current(us)',   NA,    get_param(resRx['packetJitter'], 'current', FNA), False),
                ('Inter-Frame Delay,Average(us)',   NA,    get_param(resRx['packetJitter'], 'avg', FNA), False),
                ('Inter-Frame Delay,Minimum(us)',   NA,    get_param(resRx['packetJitter'], 'min', FNA), False),
                ('Inter-Frame Delay,Maximum(us)',   NA,    get_param(resRx['packetJitter'], 'max', FNA), False),
            ]
            nvp.extend(interFrameDelay)
            
        framesizeStatistics = \
        [
            ('Frame Size Under 28 Bytes',   get_param(resTx, 'sizerunt',ICNA),  get_param(resRx, 'sizerunt',ICNA), True), 
            ('Frame Size 28-292 Bytes',     get_param(resTx, 'size29_292',ICNA), get_param(resRx, 'size29_292',ICNA), True), 
            ('Frame Size 293-556 Bytes',    get_param(resTx, 'size293_556',ICNA), get_param(resRx, 'size293_556',ICNA), True), 
            ('Frame Size 557-1084 Bytes',   get_param(resTx, 'size557_1084',ICNA), get_param(resRx, 'size557_1084',ICNA), True), 
            ('Frame Size 1085-1612 Bytes',  get_param(resTx, 'size1085_1612',ICNA),get_param(resRx, 'size1085_1612',ICNA), True), 
            ('Frame Size 1613-2140 Bytes',  get_param(resTx, 'size1613_2140',ICNA),get_param(resRx, 'size1613_2140',ICNA), True), 
            ('Frame Size Over 2140 Bytes',  get_param(resTx, 'oversize',ICNA),get_param(resRx, 'oversize',ICNA), True)
        ]
        nvp.extend(framesizeStatistics)
        
        if self.test_mode == 'FC_BERT':
            latencyStatistics = \
            [
                    ('Latency Minimum',    NA,    get_param(resRx['latency'], 'current'), False), 
                    ('Latency Average',    NA,    get_param(resRx['latency'], 'avg'), False), 
                    ('Latency Minimum',    NA,    get_param(resRx['latency'], 'min'), False),
                    ('Latency Maximum',    NA,    get_param(resRx['latency'], 'max'), False), 
            ]
            nvp.extend(latencyStatistics)

        if self.test_mode != 'FC_LOOPBACK':
            bit_error = \
            [
                    ('Bit Error',    get_param(errTx['baseErr']['bitError'], 'total',ICNA),    get_param(errRx['baseErr']['bitError'], 'total',ICNA), True), 
            ]
            nvp.extend(bit_error)

        errs_part1 = \
        [
                ('CRC Error',    get_param(errTx['baseErr'], 'fcsError',ICNA),    get_param(errRx['baseErr'], 'fcsError',ICNA), True), 
                ('Symbol Error',      NA,    get_param(errRx['baseErr'], 'symbol', ICNA), True),
                ('Disparity Error',   NA,    get_param(errRx['baseErr'], 'disparity', ICNA), True), 
        ]
        nvp.extend(errs_part1)

        if self.test_mode != 'FC_LOOPBACK':
            errs_part1_1 = \
            [
                    ('Pattern Loss',           NA,    get_param(errRx['losp'], 'total', ICNA), True), 
                    ('PATL Seconds (secs)',    NA,    get_param(errRx['losp'], 'time', FNA), True),
            ]
            nvp.extend(errs_part1_1)

        if self.test_mode != 'FC_LOOPBACK':
            errs_part3_3 = \
            [
                    ('Lost SN Error',               NA,      get_param(errRx['lof'], 'total', ICNA), True), 
                    ('Frame Rate Current (fps)',    NA,      get_param(errRx['lof'], 'curRate', FNA), False),
                    ('Frame Rate Average (fps)',    NA,      get_param(errRx['lof'], 'avgRate', FNA), False),
                    
                    ('Out SN Error',                NA,      get_param(errRx['outOfSeq'], 'total', ICNA), True), 
                    ('Frame Rate Current (fps)',    NA,      get_param(errRx['outOfSeq'], 'curRate', FNA), False),
                    ('Frame Rate Average (fps)',    NA,      get_param(errRx['outOfSeq'], 'avgRate', FNA), False),

                    ('Duplicate SN Error',          NA,      get_param(errRx['duplicate'], 'total', ICNA), True), 
                    ('Frame Rate Current (fps)',    NA,      get_param(errRx['duplicate'], 'curRate', FNA), False),
                    ('Frame Rate Average (fps)',    NA,      get_param(errRx['duplicate'], 'avgRate', FNA), False),
            ]
            nvp.extend(errs_part3_3)

        errs_part3 = \
        [
                ('LOS (Loss Of Signal)',     NA,    get_param(errRx['los'], 'total', ICNA), True), 
                ('LOS Seconds (secs)',       NA,    get_param(errRx['los'], 'time', FNA), True),
                ('LOSYNC (Loss Of Sync)',    NA,    get_param(errRx['losync'], 'total', ICNA), True),
                ('LOSYNC Seconds (secs)',    NA,    get_param(errRx['losync'], 'time', FNA), True),
        ]
        nvp.extend(errs_part3)

        others = \
        [                    
                ('NOS',                                    get_param(resTx['state'], 'NOS', ICNA),                    get_param(resRx['state'], 'NOS', ICNA), True), 
                ('OLS',                                    get_param(resTx['state'], 'OLS', ICNA),                    get_param(resRx['state'], 'OLS', ICNA), True), 
                ('LR',                                     get_param(resTx['state'], 'LR', ICNA),                get_param(resRx['state'], 'LR', ICNA), True),
                ('LRR',                                    get_param(resTx['state'], 'LRR', ICNA),               get_param(resRx['state'], 'LRR', ICNA), True), 
                ('RRDY',                                   get_param(resTx, 'r_rdy', ICNA),                      get_param(resRx, 'r_rdy', ICNA), True), 
                ('Bad SOF',                                get_param(resTx, 'bad_sof', ICNA),                    get_param(resRx, 'bad_sof', ICNA), True),
                ('Bad EOF',                                get_param(resTx, 'bad_eof', ICNA),                         get_param(resRx, 'bad_eof', ICNA), True), 
                ('Buffer-to-Buffer Credit Remaining',      get_param(resTx['B2BCredit'], 'CreditRemain', ICNA),       NA, True), 
                ('Buffer-to-Buffer Credit Used',           get_param(resTx['B2BCredit'], 'CreditUsed', ICNA),    NA, True),
        ]
        nvp.extend(others)

        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable                                    

            table.append(['Statistic Description', 'Transmitted', 'Received'])
            for n, tx_v, rx_v, bolt in nvp:
                if bolt:
                    n = Paragraph('<b>%s</b>' % n, styles["Normal"])
                table.append([n, tx_v, rx_v])
        else:       
            makeTable = self.createCsvTable

            table.append(['Statistic Description', 'Transmitted', 'Received'])
            for n, tx_v, rx_v, unused in nvp:
                table.append([n, tx_v, rx_v])
            
        makeTable(fd,"Aggregate Data",table)

    def rfc2544LatencyTableFC(self, fd, meas_data, format):            
        try:
            events = meas_data['fc_rfc2544_event'][0]['event']
            results = meas_data['result_fc_rfc2544']
        except:
            self.write_log('FC RFC2544 Latency result data not found!', 'Error')
            return
        
        if format == 'pdf':
            makeTable = self.createPdfTable
            table = [['Frame Size\n(bytes)', 'Throughput', '', 'Latency', '', '', '', '']]
            avg_string = Paragraph('<para><font>Avg (&#181;s)</font></para>', styleSheet['Normal']).getPlainText()
            min_string = Paragraph('<para><font>Min (&#181;s)</font></para>', styleSheet['Normal']).getPlainText()
            max_string = Paragraph('<para><font>Max (&#181;s)</font></para>', styleSheet['Normal']).getPlainText()
            table.append(['', 'Percentage', 'Threshold Status', \
                          'Percentage', avg_string, min_string, max_string, 'Threshold Status'])
        else:
            makeTable = self.createCsvTable
            table = []
            table.append(["Frame Size","Throughput Percentage","Throughput Threshold Status", \
                          "Latency Percentage","Latency Avg (us)","Latency Min (us)","Latency Max (us)", \
                          "Latency Threshold Status"])
        
        status = ['Pass', 'Fail', 'In Progress', 'N/A']

        #for throughput
        throughput_table = []
        quick_Latency = False
        total_page = get_param(meas_data, 'fc_rfc2544_event_page')
        cur_page = 0
        duplicate_date_check_for_throughput = {}
        while cur_page < total_page:
            events = meas_data['fc_rfc2544_event'][cur_page]['event']
            cur_page += 1
            #total = get_param(events, 'total')
            count = get_param(events, 'count')
            index = 0
            #while index < total - 1:
            while index < count:
                seq = events[str(index)]
                if get_param(seq, 'testMode') != 0 or get_param(seq, 'testStage') != 0:
                    index += 1
                    continue

                if seq['testMode'] == 0: #Trhoughput
                    threshold_st = status[seq['thresholdThroughput']]
                elif seq['testMode'] == 1: #Latency
                    threshold_st = status[seq['thresholdLatency']]
                    
                stream_size = get_param(seq, 'streamSize')
                if stream_size in duplicate_date_check_for_throughput:
                    index += 1
                    continue

                duplicate_date_check_for_throughput[stream_size] = True

                row = []
                row.extend([stream_size,
                            get_param(seq, 'frameRate', NNA), 
                            threshold_st
                            ])

                # for quick Latency mode    
                if get_param(seq, 'quickLatencyMode', 0) > 0:                    
                    quick_Latency = True
                    row.extend([
                                get_param(seq, 'frameRate'),
                                get_param(seq, 'latencyAvg'),
                                get_param(seq, 'latencyMin'),
                                get_param(seq, 'latencyMax'),
                                threshold_st
                               ])
                else:
                    row.extend(['', '', '', '', ''])
                
                throughput_table.append(row)
                index += 1

        # for normal Latency
        latency_table = []
        if not quick_Latency:
            total_page = get_param(meas_data, 'fc_rfc2544_event_page')
            cur_page = 0
            duplicate_date_check_for_latency = {}
            while cur_page < total_page:
                events = meas_data['fc_rfc2544_event'][cur_page]['event']
                cur_page += 1
                count = get_param(events, 'count')
                index = 0

                #while index < total - 1:
                while index < count:
                    seq = events[str(index)]
                    if get_param(seq, 'testMode') != 1 or get_param(seq, 'testStage') != 0:
                        index += 1
                        continue

                    stream_size = get_param(seq, 'streamSize')
                    if stream_size in duplicate_date_check_for_latency:
                        index += 1
                        continue

                    duplicate_date_check_for_latency[stream_size] = True
                        
                    row = []
                    row.extend([stream_size,'',''])
                    row.extend([
                                get_param(seq, 'frameRate'),
                                get_param(seq, 'latencyAvg'),
                                get_param(seq, 'latencyMin'),
                                get_param(seq, 'latencyMax'),
                                status[seq['thresholdLatency']]
                            ])
                    latency_table.append(row)

                    index += 1

        #merge throughput_table and latency_table
        merged_table = []
        throughput_len = len(throughput_table)
        latency_len = len(latency_table)
        if throughput_len > 0 and latency_len > 0:
            merged_len = throughput_len
            if throughput_len != latency_len:
                self.write_log('rfc2544LatencyTableFC throughput_table and latency_table has different length, can not do merge','Error')
                if merged_len > latency_len:
                    merged_len = latency_len
            for i in range(0, merged_len):
                merged_row = []
                merged_row.extend(throughput_table[i][0:3])
                merged_row.extend(latency_table[i][3:8])
                merged_table.append(merged_row)
        else:
            merged_table.extend(throughput_table)
            merged_table.extend(latency_table)

        #apply merged table
        table.extend(merged_table)
    
        style=[ \
            ('GRID',(0,0),(-1,-1),0.5, colors.grey),
            ('BOX',(0,0),(-1,-1),1, colors.grey),
            ('SPAN',(0, 0),(0, 1)),
            ('SPAN',(1,0),(2,0)),
            ('SPAN',(3,0),(7,0)),
            ('ALIGN',(0,0),(7,1),'CENTER'),
            ('VALIGN',(0,0),(0,0),'MIDDLE'),
            ('BACKGROUND', (0,0), (-1, -1), colors.lavender),
            ]

        if len(table) == 2:            
            no_data_row = ['No Data Available', '', '', '', '', '', '','']
            style.append(('SPAN', (0, 2), (7, 2)))
            table.append(no_data_row)

        makeTable(fd, "Throughput - Latency Table", table, style)

    def rfc2544FrameLossTableFC(self, fd, meas_data, format):
        try:
            events = meas_data['fc_rfc2544_event'][0]['event']
            results = meas_data['result_fc_rfc2544']
        except:
            self.write_log('FC RFC2544 FrameLoss result data not found!', 'Error')
            return

        try:            
            is_frameloss_on = results['is_frameloss_on']
            if not is_frameloss_on:
                self.write_log('frameloss must be ON!', 'Error')
                return
        except:
            self.write_log('FC RFC2544 frameLoss chart data error!', 'Error')
            return

        if format == 'pdf':
            makeTable = self.createPdfTable
        else:
            makeTable = self.createCsvTable

        table = \
        [
         ['Input Rate (%)', 'Frame Loss\nRate (%)'],
         ['']
        ]

        total_page = get_param(meas_data, 'fc_rfc2544_event_page')
        cur_page = 0
        
        old_rate = -100
        frame_line = table[1]
        current_line = []
        duplicate_date_check = {}
        while cur_page < total_page:
            events = meas_data['fc_rfc2544_event'][cur_page]['event']
            cur_page += 1

            #total = get_param(events, 'total')
            count = get_param(events, 'count')
            index = 0

            frame_line = table[1]

            #while index < total - 1:
            while index < count:
                seq = events[str(index)]
                if get_param(seq, 'testMode') != 2: 
                    index += 1
                    continue
                
                current_rate = get_param(seq, 'frameRate')
                if old_rate != current_rate:
                    current_line = [current_rate]
                    old_rate = current_rate
                    table.append(current_line)

                stream_size = get_param(seq, 'streamSize')
                if stream_size not in frame_line:
                    frame_line.append(stream_size)
                    
                framelossrate = get_param(seq, 'frameLossRate', NNA)
                if (current_rate, stream_size) not in duplicate_date_check:
                    duplicate_date_check[(current_rate, stream_size)] = framelossrate
                    current_line.append(framelossrate)
                
                index += 1

        row_len = len(table[1])
        if row_len < 2: row_len = 2
        
        table[0].extend([''] * (row_len - 2))
        
        style = \
        [ 
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0),(-1, -1), 1, colors.grey),
            ('SPAN', (0, 0), (0, 1)),
            ('SPAN', (1, 0), (row_len - 1, 0)),
            ('ALIGN', (1, 0), (row_len -1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (0, 1), 'MIDDLE'),
            ('BACKGROUND', (0,0), (-1, -1), colors.lavender),
        ]

        if len(table) == 2:
            table[1] = ['', 'No Data Available']
        
        for row in table:
            line_len = len(row)
            row.extend([''] * (row_len - line_len))

        makeTable(fd, "Frame Loss Table", table, style)

    def rfc2544Back2BackTableFC(self, fd, meas_data, format):
        try:
            events = meas_data['fc_rfc2544_event'][0]['event']
            results = meas_data['result_fc_rfc2544']
        except:
            self.write_log('FC RFC2544 Back2Back result data not found!', 'Error')
            return
        
        if format == 'pdf':
            makeTable = self.createPdfTable
        else:
            makeTable = self.createCsvTable
            
        table = []
        table.append(["Frame Size (bytes)","Average","Minimum","Maximum"])

        fs = []

        
        total_page = get_param(meas_data, 'fc_rfc2544_event_page')
        cur_page = 0

        while cur_page < total_page:
            events = meas_data['fc_rfc2544_event'][cur_page]['event']
            cur_page += 1

            #total = get_param(events, 'total')
            count = get_param(events, 'count')
            index = 0
            #while index < total - 1:
            while index < count:
                seq = events[str(index)]
                if get_param(seq, 'testMode') != 3:
                    index += 1
                    continue
                
                ss = get_param(seq,'streamSize')
                if ss in fs:
                    index += 1
                    continue
                fs.append(ss)
                
                table.append([ss,
                            #get_param(seq,'frameAvg', ICNA),
                            curnum_to_string(long(seq['frameAvg']), True),
                            get_param(seq,'frameMin', ICNA),
                            get_param(seq,'frameMax', ICNA)
                            #get_param(seq['backToBack'],'status')
                            ])
                index += 1

        style= \
            [
                ('GRID',(0,0),(-1,-1), 0.5, colors.grey),
                ('BOX',(0,0),(-1,-1), 1, colors.grey),
                ('BACKGROUND', (0,0), (-1, -1), colors.lavender),
            ]
        if len(table) == 1:            
            no_data_row = ['No Data Available', '', '', '']
            style.append(('SPAN', (0, 1), (3, 1)))
            table.append(no_data_row)
            
        makeTable(fd, "Back to Back Table", table, style)

    def throughPutChartFC(self, lst, meas_data):
        try:
            events = meas_data['fc_rfc2544_event'][0]['event']
            results = meas_data['result_fc_rfc2544']
        except:
            self.write_log('FC RFC2544 Througput chart data not found!', 'Error')
            return
        
        try:            
            is_throughput_on = results['is_throughput_on']
            if not is_throughput_on:
                self.write_log('Throuput must be ON!')
                header = 'Throughput Chart'
                lst.append(Paragraph(header, styleSheet['Heading2']))
                lst.append(Paragraph("No data available the chart is not displayed", styleSheet['BodyText']))
                return
        except:
           self.write_log('RFC2544 Througput chart data error!', 'Error')
           return

        try:            
            drawing = Drawing(400, 200)
            data = [[]]
            columns = []
    
            total_page = get_param(meas_data, 'fc_rfc2544_event_page')
            cur_page = 0
            while cur_page < total_page:
                events = meas_data['fc_rfc2544_event'][cur_page]['event']
                cur_page += 1

                #total = get_param(events, 'total')
                count = get_param(events, 'count')
                index = 0
                #while index < total - 1:
                while index < count - 1:
                    seq = events[str(index)]
                    if get_param(seq, 'testMode') != 0 or get_param(seq, 'testStage') != 0: 
                        index += 1
                        continue
        
                    columns.append(str(get_param(seq, 'streamSize')))
                    value = int(float(get_param(seq, 'frameRate')))
                    data[0].append(-2 if value == 0 else value)
                    index += 1
                    
            bc = VerticalBarChart()
            bc.x = 50
            bc.y = 50
            bc.height = 125
            bc.width = 300
            bc.data = data
            bc.strokeColor = colors.black
            bc.valueAxis.valueMin = -3
            bc.valueAxis.valueMax = 100
            bc.valueAxis.valueStep = 10
            bc.categoryAxis.labels.boxAnchor = 'ne'
            bc.categoryAxis.labels.dx = 8
            bc.categoryAxis.labels.dy = -2
            bc.categoryAxis.labels.angle = 30
            bc.categoryAxis.categoryNames = columns
            bc.barLabels.fontName = 'Helvetica'
            bc.bars[0].fillColor = colors.darkturquoise
            bc.bars[1].fillColor = colors.green
            bc.bars[2].fillColor = colors.red
            bc.bars[3].fillColor = colors.darksalmon
                
            drawing.add(bc)      
    
            header = 'Throughput Chart'
            lst.append(Paragraph(header, styleSheet['Heading2']))
                  
            lst.append(drawing)
            lst.append(Paragraph("Legend: Y axis = Frame Rate in percent, X axis = Frame Size", styleSheet['BodyText']))
        except:
           self.write_log('RFC2544 Througput chart generation error!', 'Error')
           return

    def frameLossChartFC(self, lst, meas_data):
        try:
            events = meas_data['fc_rfc2544_event'][0]['event']
            results = meas_data['result_fc_rfc2544']
        except:
            self.write_log('FC RFC2544 frameLoss chart data not found!', 'Error')
            return
        
        try:            
            is_frameloss_on = results['is_frameloss_on']
            if not is_frameloss_on:
                self.write_log('frameloss must be ON!')
                header = 'Frame Loss Chart'
                lst.append(Paragraph(header, styleSheet['Heading2']))
                lst.append(Paragraph("No data available the chart is not displayed", styleSheet['BodyText']))
                return
        except:
            self.write_log('FC RFC2544 frameLoss chart data error!', 'Error')
            return

        try:            
            drawing = Drawing(400, 200)
            rates = []
            streams = []
            row = []
            data = []

            total_page = get_param(meas_data, 'fc_rfc2544_event_page')
            cur_page = 0
            while cur_page < total_page:
                events = meas_data['fc_rfc2544_event'][cur_page]['event']
                cur_page += 1
            
                #total = get_param(events, 'total')
                count = get_param(events, 'count')
                
                index = 0
                #while index < total:
                while index < count:
                    seq = events[str(index)]
                    if get_param(seq, 'testMode') != 2: 
                        index += 1
                        continue
                    
                    rate = get_param(seq, 'frameRate')
                    if rate not in rates:
                        rates.append(rate)
                    
                    size = get_param(seq, 'streamSize')
                    if size not in streams: 
                        streams.append(size)
                    
                    row.append(int(float(get_param(seq, 'frameLossRate'))))
                    index += 1
            
            col_max = 10
            col_count = len(rates)
            row_count = len(streams)
            rates = ['10', '20', '30', '40', '50', '60', '70', '80', '90', '100']       
            
            i = 0
            while i < (row_count + 2):            
                data.append([0] * col_max) # not * - deep array copy needed  
                i += 1
    
            index = 0
            for value in row:
                i = int(index / row_count)
                j = index - i * row_count + 1
                value = row[index]
                if value == 0: value = -2
                data[j][i] = value
                #print row_count, index, i, j, data[j][i]
                index += 1
            
            i = 0
            while i < (row_count + 2):            
                data[i].reverse()
                i += 1
                    
            bc = VerticalBarChart()
            bc.x = 50
            bc.y = 50
            bc.height = 125
            bc.width = 300
            bc.data = data
            bc.strokeColor = colors.black
            bc.valueAxis.valueMin = -3
            bc.valueAxis.valueMax = 100
            bc.valueAxis.valueStep = 25
            bc.categoryAxis.labels.boxAnchor = 'ne'
            bc.categoryAxis.labels.dx = 8
            bc.categoryAxis.labels.dy = -2
            bc.categoryAxis.labels.angle = 30
            bc.categoryAxis.categoryNames = rates
            bc.bars[0].fillColor = colors.red
            bc.bars[1].fillColor = colors.red
            bc.bars[2].fillColor = colors.blue        
            bc.bars[3].fillColor = colors.green
            bc.bars[4].fillColor = colors.grey
            bc.bars[5].fillColor = colors.pink
            bc.bars[6].fillColor = colors.brown
            bc.bars[7].fillColor = colors.cyan
            bc.bars[8].fillColor = colors.lightgreen
            bc.bars[9].fillColor = colors.goldenrod
            bc.bars[10].fillColor = colors.lightcoral
            bc.bars[11].fillColor = colors.lightcoral
                
            drawing.add(bc)
            
            header = 'Frame Loss Chart'
            lst.append(Paragraph(header, styleSheet['Heading2']))
            lst.append(drawing)
            lst.append(Paragraph("Legend: Y axis = Frame Loss Rate in Percent, X axis = Frame Rate", styleSheet['BodyText']))
            lst.append(Paragraph("Bar Chart Colors for Frame Size in Bytes:", styleSheet['BodyText']))
        
            my_colors = ['red', 'blue', 'green', 'grey', 'pink', 'brown', \
                         'cyan', 'lightgreen', 'goldenrod', 'lightcoral']
            footnote = '<para>'
            for f_size, my_color in zip(streams, my_colors):
                footnote += '<font color=\'%s\'>%s</font> | ' % (my_color, f_size)
            footnote = footnote.rstrip(' | ')
            footnote += '</para>'
            lst.append(Paragraph(footnote,  styleSheet['BodyText']))
        except:
            self.write_log('RFC2544 frameLoss chart gereration error!', 'Error')
            return


    def StreamResultTables(self, fd, meas_data, format):
        #bug 12907
        utilLineRate = 'Utilized Line Rate (%s)'
        infoRate = 'Information Rate (%s)'
        
        nvp_part1 = \
        [
            ('Total Frames',                'txStats/totalFrames', 'rxStats/totalFrames', 'total', True, ICNA, ICNA), 
            ('Total Bytes',                 'txStats/totalBytes', 'rxStats/totalBytes', 'total', True, ICNA, ICNA), 
            ('Frame Rate Current (fps)',    'txStats/totalFrames', 'rxStats/totalFrames', 'curRate', False, NNA, NNA), 
            ('Frame Rate Average (fps)',    'txStats/totalFrames', 'rxStats/totalFrames', 'avgRate', False, NNA, NNA), 
            ('Frame Rate Minimum (fps)',    'txStats/totalFrames', 'rxStats/totalFrames', 'minRate', False, NNA, NNA), 
            ('Frame Rate Maximum (fps)',    'txStats/totalFrames', 'rxStats/totalFrames', 'maxRate', False, NNA, NNA), 
            ('Utilized Line Rate Current (%)',     'txStats/totalBytes', 'rxStats/totalBytes', 'curUtil', False, NNA, NNA), 
            ('Utilized Line Rate Average (%)',     'txStats/totalBytes', 'rxStats/totalBytes', 'avgUtil', False, NNA, NNA), 
            ('Utilized Line Rate Minimum (%)',     'txStats/totalBytes', 'rxStats/totalBytes', 'minUtil', False, NNA, NNA), 
            ('Utilized Line Rate Maximum (%)',     'txStats/totalBytes', 'rxStats/totalBytes', 'maxUtil', False, NNA, NNA), 
            (utilLineRate,                  'txStats', 'rxStats', 'lineRate', False, NNA, NNA), 
            (infoRate,                      'txStats', 'rxStats', 'dataRate', False, NNA, NNA), 
            ('Frame Size Under 64 Bytes',   'txStats', 'rxStats', 'fsz63', True, ICNA, ICNA), 
            ('Frame Size 64 Bytes',         'txStats', 'rxStats', 'fsz64', True, ICNA, ICNA), 
            ('Frame Size 65-127 Bytes',     'txStats', 'rxStats', 'fsz128', True, ICNA, ICNA), 
            ('Frame Size 128-255 Bytes',    'txStats', 'rxStats', 'fsz256', True, ICNA, ICNA), 
            ('Frame Size 256-511 Bytes',    'txStats', 'rxStats', 'fsz512', True, ICNA, ICNA), 
            ('Frame Size 512-1023 Bytes',   'txStats', 'rxStats', 'fsz1024', True, ICNA, ICNA), 
            ('Frame Size 1024-1518 Bytes',  'txStats', 'rxStats', 'fsz1518', True, ICNA, ICNA), 
            ('Frame Size Over 1518 Bytes',  'txStats', 'rxStats', 'fsz1519', True, ICNA, ICNA),
            #('Test Frames', 'txtestframes', 'rxtestframes',0), 
            #('Frame Rate Current (fps)', 'txtestfrcur', 'rxtestfrcur',2), 
            #('Frame Rate Average (fps)', 'txtestfravg', 'rxtestfravg',2),
            #('Non Test Frames', 'dummy', 'rxnontestframes',0), 
            #('Frame Rate Current (fps)', 'dummy', 'rxntestfrcur',2), 
            #('Frame Rate Average (fps)', 'dummy', 'rxntestfravg',2),
            ('Total Unicast Frames',        'txStats/uMacFrames', 'rxStats/uMacFrames', 'total', True, ICNA, ICNA), 
            ('Frame Rate Current (fps)',    'txStats/uMacFrames', 'rxStats/uMacFrames', 'curRate', False, NNA, NNA), 
            ('Frame Rate Average (fps)',    'txStats/uMacFrames', 'rxStats/uMacFrames', 'avgRate', False, NNA, NNA), 
            ('Total Multicast Frames',      'txStats/mMacFrames', 'rxStats/mMacFrames', 'total', True, ICNA, ICNA), 
            ('Frame Rate Current (fps)',    'txStats/mMacFrames', 'rxStats/mMacFrames', 'curRate', False, NNA, NNA), 
            ('Frame Rate Average (fps)',    'txStats/mMacFrames', 'rxStats/mMacFrames', 'avgRate', False, NNA, NNA), 
            ('Total Broadcast Frames',      'txStats/bMacFrames', 'rxStats/bMacFrames', 'total', True, ICNA, ICNA), 
            ('Frame Rate Current (fps)',    'txStats/bMacFrames', 'rxStats/bMacFrames', 'curRate', False, NNA, NNA), 
            ('Frame Rate Average (fps)',    'txStats/bMacFrames', 'rxStats/bMacFrames', 'avgRate', False, NNA, NNA), 
            ('Total Invalid Frames',        'dummy', 'rxStats/invalidMacFrames', 'total', True, NA, NNA), 
            ('Frame Rate Current (fps)',    'dummy', 'rxStats/invalidMacFrames', 'curRate', False, NA, NNA), 
            ('Frame Rate Average (fps)',    'dummy', 'rxStats/invalidMacFrames', 'avgRate', False, NA, NNA), 
            ('Total VLAN Frames',           'txStats/totalVlanFrames', 'rxStats/totalVlanFrames', 'total', True, ICNA, ICNA), 
            ('Frame Rate Current (fps)',    'txStats/totalVlanFrames', 'rxStats/totalVlanFrames', 'curRate', False, NNA, NNA), 
            ('Frame Rate Average (fps)',    'txStats/totalVlanFrames', 'rxStats/totalVlanFrames', 'avgRate', False, NNA, NNA), 
            ('Total Single-Tagged VLAN Frames', 'txStats/sVlanFrames', 'rxStats/sVlanFrames', 'total', True, ICNA, ICNA), 
            ('Frame Rate Current (fps)',    'txStats/sVlanFrames', 'rxStats/sVlanFrames', 'curRate', False, NNA, NNA), 
            ('Frame Rate Average (fps)',    'txStats/sVlanFrames', 'rxStats/sVlanFrames', 'avgRate', False, NNA, NNA), 
            ('Total Multi-Tagged VLAN Frames', 'txStats/mVlanFrames', 'rxStats/mVlanFrames', 'total', True, ICNA, ICNA), 
            ('Frame Rate Current (fps)',    'txStats/mVlanFrames', 'rxStats/mVlanFrames', 'curRate', False, NNA, NNA), 
            ('Frame Rate Average (fps)',    'txStats/mVlanFrames', 'rxStats/mVlanFrames', 'avgRate', False, NNA, NNA), 
            ('Total MPLS Frames',           'txStats/mplsFrames', 'rxStats/mplsFrames', 'total', True, ICNA, ICNA), 
            ('Frame Rate Current (fps)',    'txStats/mplsFrames', 'rxStats/mplsFrames', 'curRate', False, NNA, NNA), 
            ('Frame Rate Average (fps)',    'txStats/mplsFrames', 'rxStats/mplsFrames', 'avgRate', False, NNA, NNA), 
            ('Total IPv4 Frames',           'txStats/ipv4Frames', 'rxStats/ipv4Frames', 'total', True, ICNA, ICNA), 
            ('Frame Rate Current (fps)',    'txStats/ipv4Frames', 'rxStats/ipv4Frames', 'curRate', False, NNA, NNA), 
            ('Frame Rate Average (fps)',    'txStats/ipv4Frames', 'rxStats/ipv4Frames', 'avgRate', False, NNA, NNA), 
            ('Total Unicast IPv4 Frames',   'txStats/uIpv4Frames', 'rxStats/uIpv4Frames', 'total', True, ICNA, ICNA), 
            ('Frame Rate Current (fps)',    'txStats/uIpv4Frames', 'rxStats/uIpv4Frames', 'curRate', False, NNA, NNA), 
            ('Frame Rate Average (fps)',    'txStats/uIpv4Frames', 'rxStats/uIpv4Frames', 'avgRate', False, NNA, NNA), 
            ('Total Multicast IPv4 Frames', 'txStats/mIpv4Frames', 'rxStats/mIpv4Frames', 'total', True, ICNA, ICNA), 
            ('Frame Rate Current (fps)',    'txStats/mIpv4Frames', 'rxStats/mIpv4Frames', 'curRate', False, NNA, NNA), 
            ('Frame Rate Average (fps)',    'txStats/mIpv4Frames', 'rxStats/mIpv4Frames', 'avgRate', False, NNA, NNA), 
            ('Total Broadcast IPv4 Frames', 'txStats/bIpv4Frames', 'rxStats/bIpv4Frames', 'total', True, ICNA, ICNA), 
            ('Frame Rate Current (fps)',    'txStats/bIpv4Frames', 'rxStats/bIpv4Frames', 'curRate', False, NNA, NNA), 
            ('Frame Rate Average (fps)',    'txStats/bIpv4Frames', 'rxStats/bIpv4Frames', 'avgRate', False, NNA, NNA), 
        ]

        nvp_part2 = \
        [
            ('Total TCP Frames',            'txStats/tcpFrames', 'rxStats/tcpFrames', 'total', True, ICNA, ICNA), 
            ('Frame Rate Current (fps)',    'txStats/tcpFrames', 'rxStats/tcpFrames', 'curRate', False, NNA, NNA), 
            ('Frame Rate Average (fps)',    'txStats/tcpFrames', 'rxStats/tcpFrames', 'avgRate', False, NNA, NNA), 
            ('Total UDP Frames',            'txStats/udpFrames', 'rxStats/udpFrames', 'total', True, ICNA, ICNA), 
            ('Frame Rate Current (fps)',    'txStats/udpFrames', 'rxStats/udpFrames', 'curRate', False, NNA, NNA), 
            ('Frame Rate Average (fps)',    'txStats/udpFrames', 'rxStats/udpFrames', 'avgRate', False, NNA, NNA), 
        ]

        nvp_pauseframes = \
        [
            ('Total Pause Frames',          'txStats/pauseFrames', 'rxStats/pauseFrames', 'total', True, ICNA, ICNA), 
        ]

        jitter_nvp = \
        [            
            (Paragraph('<para><font>Frame Delay Variation Minimum (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), 'dummy', 'rxStats/packetJitter', 'min', True, NA, NNA),
            (Paragraph('<para><font>Frame Delay Variation Maximum (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), 'dummy', 'rxStats/packetJitter', 'max', True, NA, NNA),
            (Paragraph('<para><font>Frame Delay Variation Average (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), 'dummy', 'rxStats/packetJitter', 'avg', True, NA, NNA),
        ]
        
        more_nvp1 = \
        [
            (Paragraph('<para><font>Frame Gap Minimum (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), 'dummy', 'rxStats/frameGap', 'min', True, NA, NNA),
            (Paragraph('<para><font>Frame Gap Maximum (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), 'dummy', 'rxStats/frameGap', 'max', True, NA, NNA),
            (Paragraph('<para><font>Frame Gap Average (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), 'dummy', 'rxStats/frameGap', 'avg', True, NA, NNA),
            ('Service Disruption Events', 'dummy', 'rxStats/servDisrupt', 'events', True, NA, NNA),
            (Paragraph('<para><font>Service Disruption Duration (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), 'dummy', 'rxStats/servDisrupt', 'duration', True, NA, NNA),
            (Paragraph('<para><font>Service Disruption Min (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), 'dummy', 'rxStats/servDisrupt', 'min', True, NA, NNA),
            (Paragraph('<para><font>Service Disruption Max (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), 'dummy', 'rxStats/servDisrupt', 'max', True, NA, NNA),
            (Paragraph('<para><font>Service Disruption Avg (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), 'dummy', 'rxStats/servDisrupt', 'avg', True, NA, NNA),
            (Paragraph('<para><font>Latency Minimum (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), 'dummy', 'rxStats/latency', 'min', True, NA, NNA),
            (Paragraph('<para><font>Latency Maximum (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), 'dummy', 'rxStats/latency', 'max', True, NA, NNA),
            (Paragraph('<para><font>Latency Average (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), 'dummy', 'rxStats/latency', 'avg', True, NA, NNA),
        ]
        
        nvp_losevent = \
        [
            ('LOS Event',                   'dummy', 'rxError/los', 'total', True, NA, NNA), 
            ('LOSS Aggregate (secs)',       'dummy', 'rxError/los', 'time', True, NA, NNA), 
            ('LOSS Minimum (secs)',         'dummy', 'rxError/los', 'min', True, NA, NNA), 
            ('LOSS Maximum (secs)',         'dummy', 'rxError/los', 'max', True, NA, NNA), 
            ('LOSS Current (secs)',         'dummy', 'rxError/los', 'cur', True, NA, NNA), 
            ('LOSS Average (secs)',         'dummy', 'rxError/los', 'avg', True, NA, NNA),
            ('LOSync Event',                'dummy', 'rxError/los', 'total', True, NA, NNA), 
            ('LOSync Aggregate (secs)',     'dummy', 'rxError/los', 'time', True, NA, NNA), 
            ('LOSync Minimum (secs)',       'dummy', 'rxError/los', 'min', True, NA, NNA), 
            ('LOSync Maximum (secs)',       'dummy', 'rxError/los', 'max', True, NA, NNA), 
            ('LOSync Current (secs)',       'dummy', 'rxError/los', 'cur', True, NA, NNA), 
            ('LOSync Average (secs)',       'dummy', 'rxError/los', 'avg', True, NA, NNA),
        ]

        more_nvp2_stream = \
        [
            ('Total FCS/CRC Error',         'txError/fcsError', 'rxError/fcsError', 'total', True, ICNA, ICNA), 
            ('Frame Rate Current (fps)',    'txError/fcsError', 'rxError/fcsError', 'curRate', False, NNA, NNA), 
            ('Frame Rate Average (fps)',    'txError/fcsError', 'rxError/fcsError', 'avgRate', False, NNA, NNA),
            ('Total IP Checksum Error',     'dummy', 'rxError/ipChecksumError', 'total', True, NA, ICNA), 
            ('Frame Rate Current (fps)',    'dummy', 'rxError/ipChecksumError', 'curRate', False, NA, NNA), 
            ('Frame Rate Average (fps)',    'dummy', 'rxError/ipChecksumError', 'avgRate', False, NA, NNA), 
            ('Total TCP Checksum Error',    'dummy', 'rxError/tcpChecksumError', 'total', True, NA, ICNA), 
            ('Frame Rate Current (fps)',    'dummy', 'rxError/tcpChecksumError', 'curRate', False, NA, NNA), 
            ('Frame Rate Average (fps)',    'dummy', 'rxError/tcpChecksumError', 'avgRate', False, NA, NNA), 
            ('Total UDP Checksum Error',    'dummy', 'rxError/udpChecksumError', 'total', True, NA, ICNA), 
            ('Frame Rate Current (fps)',    'dummy', 'rxError/udpChecksumError', 'curRate', False, NA, NNA), 
            ('Frame Rate Average (fps)',    'dummy', 'rxError/udpChecksumError', 'avgRate', False, NA, NNA),
            #('Lost SN Error',               'txError/lostSnError','rxError/lostSnError', 'current', False),
            ('Total Frame Loss Error',      'dummy', 'rxError/lostSnError', 'total', True, NA, ICNA),
            ('Frame Rate Current (fps)',    'dummy', 'rxError/lostSnError', 'curRate', False, NA, NNA),
            ('Frame Rate Average (fps)',    'dummy', 'rxError/lostSnError', 'avgRate', False, NA, NNA),
            ('Total Out of Sequence Error', 'dummy', 'rxError/outOfSeqError', 'total', True, NA, ICNA),
            ('Frame Rate Current (fps)',    'dummy', 'rxError/outOfSeqError', 'curRate', False, NA, NNA),
            ('Frame Rate Average (fps)',    'dummy', 'rxError/outOfSeqError', 'avgRate', False, NA, NNA),
            ('Total Duplicate Sequence Error',    'dummy', 'rxError/dupSnError', 'total', True, NA, ICNA),
            ('Frame Rate Current (fps)',    'dummy', 'rxError/dupSnError', 'curRate', False, NA, NNA),
            ('Frame Rate Average (fps)',    'dummy', 'rxError/dupSnError', 'avgRate', False, NA, NNA),
            ('Bit Error',                   'txError/bitError', 'rxError/bitError', 'total', True, ICNA, ICNA),
            ('Current Bit',                 'txError/bitError', 'rxError/bitError', 'current', False, ICNA, ICNA),
            ('Current Bit Error Rate',      'txError/bitError', 'rxError/bitError', 'curBitRate', False, EXP, EXP),
            ('Bit Error Rate',              'txError/bitError', 'rxError/bitError', 'bitRate', False, EXP, EXP),
            ('LOPS (secs)',                 'txError/bitError', 'rxError/bitError', 'lopsTime', False, NNA, NNA),
            ('No BERT Traffic (secs)',      'txError/bitError', 'rxError/bitError', 'noBertTraffic', False, NNA, NNA),
        ]

        nvp_streams = []
        nvp_streams.extend(nvp_part1)
        nvp_streams.extend(nvp_part2)
        nvp_streams.extend(nvp_pauseframes)
        nvp_streams.extend(jitter_nvp)
        nvp_streams.extend(more_nvp1)
        nvp_streams.extend(more_nvp2_stream)
        
        nvp_nonstreams = []
        nvp_nonstreams.extend(nvp_part1)
        nvp_nonstreams.extend(nvp_part2)

        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            
            for i in meas_data['result']:
                if i == 0: continue; #agregate
                if meas_data['result'][i] is None: continue
                stream = meas_data['result'][i]['eth']
                if i != 17 and i > stream['totalsno']:
                    continue

                if stream['sno'] == 17:
                    nvp = nvp_nonstreams
                    table = []
                    table.append(['Statistic Description', 'Received'])
                    for row in nvp:
                        tx_fmt = rx_fmt = NA
                        if len(row) > 5:
                            n, tx_path, rx_path, node, bolt, tx_fmt, rx_fmt = row
                        else:
                            n, tx_path, rx_path, node, bolt = row                    
                        if bolt:
                            n = Paragraph('<b>%s</b>' % n, styles["Normal"])
                        #bug 12907
                        if n in (utilLineRate, infoRate):
                            n, val1, val2 = fbps4(n, get_param_from_path(stream, tx_path, node, tx_fmt, False), 
                                                  get_param_from_path(stream, rx_path, node, rx_fmt, False))
                            table.append([n, val2])
                        else:                        
                            table.append( 
                                [
                                    n,
                                    get_param_from_path(stream, rx_path, node, rx_fmt),
                                ])
                else:
                    nvp = nvp_streams
                    table = []
                    table.append(['Statistic  Description', 'Transmitted', 'Received'])
                    for row in nvp:
                        tx_fmt = rx_fmt = NA
                        if len(row) > 5:
                            n, tx_path, rx_path, node, bolt, tx_fmt, rx_fmt = row
                        else:
                            n, tx_path, rx_path, node, bolt = row                    
                        if bolt:
                            n = Paragraph('<b>%s</b>' % n, styles["Normal"])
                        #bug 12907
                        if n in (utilLineRate, infoRate):
                            n, val1, val2 = fbps4(n, get_param_from_path(stream, tx_path, node, tx_fmt, False), 
                                                  get_param_from_path(stream, rx_path, node, rx_fmt, False))
                            table.append([n, val1, val2])
                        else:                        
                            table.append( 
                                [
                                    n,
                                    get_param_from_path(stream, tx_path, node, tx_fmt),
                                    get_param_from_path(stream, rx_path, node, rx_fmt),
                                ])
                
                if stream['sno'] == 17:
                    makeTable(fd,"Non Test Stream Data", table)
                else:
                    makeTable(fd,"Stream %d Data" % stream['sno'], table)
        else:
            makeTable = self.createCsvTable
            
            for i in meas_data['result']:
                if i == 0: continue; #agregate
                if meas_data['result'][i] is None: continue
                stream = meas_data['result'][i]['eth']
                if i != 17 and i > stream['totalsno']:
                    continue

                if stream['sno'] == 17:
                    nvp = nvp_nonstreams
                    table = []
                    table.append(['Statistic Description', 'Received'])
                    for row in nvp:
                        tx_fmt = rx_fmt = NA
                        if len(row) > 5:
                            n, tx_path, rx_path, node, unused, tx_fmt, rx_fmt = row
                        else:
                            n, tx_path, rx_path, node, unused = row                    
                        #bug 12907
                        if n in (utilLineRate, infoRate):
                            n, val1, val2 = fbps4(n, get_param_from_path(stream, tx_path, node, tx_fmt, False), 
                                                  get_param_from_path(stream, rx_path, node, rx_fmt, False))
                            table.append([n, val2])
                        else:                        
                            table.append( 
                                [
                                    n,
                                    get_param_from_path(stream, rx_path, node, rx_fmt),
                                ])
                else:
                    nvp = nvp_streams
                    table = []
                    table.append(['Statistic  Description', 'Transmitted', 'Received'])
                    for row in nvp:
                        tx_fmt = rx_fmt = NA
                        if len(row) > 5:
                            n, tx_path, rx_path, node, unused, tx_fmt, rx_fmt = row
                        else:
                            n, tx_path, rx_path, node, unused = row                    

                        #bug 12907
                        if n in (utilLineRate, infoRate):
                            n, val1, val2 = fbps4(n, get_param_from_path(stream, tx_path, node, tx_fmt, False), 
                                                  get_param_from_path(stream, rx_path, node, rx_fmt, False))
                            table.append([n, val1, val2])
                        else:                        
                            table.append( 
                                [
                                    n,
                                    get_param_from_path(stream, tx_path, node, tx_fmt),
                                    get_param_from_path(stream, rx_path, node, rx_fmt),
                                ])
                
                if stream['sno'] == 17:
                    makeTable(fd,"Non Test Stream Data", table)
                else:
                    makeTable(fd,"Stream %d Data" % stream['sno'], table)

    def wanResultTable(self, fd, wan_result, ports, format):
        result = wan_result['result']
        if ports == 'WANSDH':
            table_name = 'WAN SDH Data'
            nvp = \
                [
                    ('RS',''),
                    ('LOS (seconds)',get_param(result,'los', ICNA)),
                    ('LOF (seconds)',get_param(result,'lof', ICNA)),
                    ('OOF (seconds)',get_param(result,'oof', ICNA)),
                    ('B1',get_param(result,'b1', ICNA)),
                    ('MS',''),
                    ('MS-AIS (seconds)',get_param(result,'msais', ICNA)),
                    ('MS-RDI (seconds)',get_param(result,'msrdi', ICNA)),
                    ('B2',get_param(result,'b2', ICNA)),
                    ('MS-REI',get_param(result,'msrei', ICNA)),
                    ('PATH',''),
                    ('AU-AIS (seconds)',get_param(result,'auais', ICNA)),
                    ('AU-LOP (seconds)',get_param(result,'aulop', ICNA)),
                    ('HP-UNEQ (seconds)',get_param(result,'hpuneq', ICNA)),
                    ('HP-PLM (seconds)',get_param(result,'hpplm', ICNA)),
                    ('HP-RDI (seconds)',get_param(result,'hprdi', ICNA)),
                    
                    ('B3',get_param(result,'b3', ICNA)),
                    ('HP-REI',get_param(result,'hprei', ICNA)),
                ]
        elif ports == 'WANSONET': 
            table_name = 'WAN SONET Data'
            nvp = \
                [
                    ('SECTION',''),
                    ('LOS (seconds)',get_param(result,'los', ICNA)),
                    ('LOF (seconds)',get_param(result,'lof', ICNA)),
                    ('OOF (seconds)',get_param(result,'oof', ICNA)),
                    ('B1',get_param(result,'b1', ICNA)),
                    ('LINE',''),
                    ('AIS-L (seconds)',get_param(result,'msais', ICNA)),
                    ('RDI-L (seconds)',get_param(result,'msrdi', ICNA)),
                    ('B2',get_param(result,'b2', ICNA)),
                    ('REI-L',get_param(result,'msrei', ICNA)),
                    ('PATH',''),
                    ('AIS-P (seconds)',get_param(result,'auais', ICNA)),
                    ('LOP-P (seconds)',get_param(result,'aulop', ICNA)),
                    ('UNEQ-P (seconds)',get_param(result,'hpuneq', ICNA)),
                    ('PLM-P (seconds)',get_param(result,'hpplm', ICNA)),
                    ('RDI-P (seconds)',get_param(result,'hprdi', ICNA)),
                    
                    ('B3',get_param(result,'b3', ICNA)),
                    ('REI-P',get_param(result,'hprei', ICNA)),
                ]
        else:
            table_name = ''
            nvp = []
            return
                        
        table = [['Alarm','Duration/Count']]
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n,v in nvp:
                table.append([n,v])
        else:
            makeTable = self.createCsvTable
            for n,v in nvp:
                table.append([n,v])

        makeTable(fd, table_name, table)


    def bertSetupFC(self, fd, config, format):
        try:
            setup = config['config']['ether']['stFCBertConfig']
        except:
            self.write_log('FC Bert setup data not found!', 'Error')
            return                       

        #FC Bert Test Setup       
        self.throughputTestSetupFC(fd, setup, format)

        test_layer = get_param(setup, 'testLayer')
        if test_layer == 'FC_FC1':
            self.throughputStreamPayloadFC(fd, setup, format)
        #FC Bert Stream Setup         
        elif test_layer == 'FC_FC2':
            self.throughputStreamFrameSetupFC(fd, setup, format)
            pattern = setup['stream']['pattern']['type']
            if pattern != 'CJPAT' and pattern != 'CRPAT':
                self.throughputStreamFrameHeaderFC(fd, setup, format)
            self.throughputStreamPayloadFC(fd, setup, format)
            self.throughputStreamTrafficSetupFC(fd, setup, format)
                                        
        self.write_log("END FC Bert Setup %s"%format)

    def throughputTestSetupFC(self, fd, setup, format):
        test_type = get_param(setup,'testType')
        if test_type == 'BERT':
            test_type = 'Bert Traffic'
        else:
            test_type = 'Live Traffic'
       
        test_layer = get_param(setup, 'testLayer')
        try:
            if self.testport == 'SFP':
                test_layer = {'FC_FC1': 'FC-1', 'FC_FC2': 'FC-2'}[test_layer]
            else:
                test_layer = NA
        except:
            test_layer = NA
            self.write_log("Problem setting FC BERT layer")
        
        nvp = \
            [ 
                ('Test Type',test_type),
                ('Test Layer',test_layer),
            ]
        
        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n, v in nvp:
                table.append([n,v])            
        else:
            makeTable = self.createCsvTable
            for n, v in nvp:
                table.append([n,v])
            
        makeTable(fd, "Throughput Test Setup", table)

    def throughputStreamFrameSetupFC(self, fd, setup, format, isThroughput = True):               
        table = []
        names_inserted = False

        tablename = "Frame Setup"
        if isThroughput:
            stream_table = setup['stream']
            tablename = "FC-2 - " + tablename
        else:
            stream_table = setup['streamTable'][0]

        b2bOn = 'Off'
        if stream_table['b2b_flag'] != 0: b2bOn = 'On'

        nvp = []
        nvp1 = \
            [
                ('Frame Length', stream_table['frameLength']['constFrameLength'])
            ]
        nvp2 = \
            [
                #('Class Of Service', stream_table['cos']),
                ('Class Of Service', 3),
                ('B-TO-B Credit Management',b2bOn),
                ('B-TO-B Credit', stream_table['b2b_credit'])
            ]
        if isThroughput:
            nvp.extend(nvp1)
            pattern = stream_table['pattern']['type']
            if pattern != 'CJPAT' and pattern != 'CRPAT':
                nvp.extend(nvp2)
        else:
            nvp.extend(nvp2)

        if format == 'pdf':
            makeTable = self.createPdfTable
            for n,v in nvp:
                table.append([n,v])        
        else:
            makeTable = self.createCsvTable
            for n,v in nvp:
                table.append([n,v])   

        makeTable(fd, tablename, table)
        
    def throughputStreamFrameHeaderFC(self, fd, setup, format, isThroughput = True):               
        table = []
        names_inserted = False   

        tablename = "Frame Header"
        if isThroughput:
            frameheader = setup['stream']['header']
            tablename = "FC-2 - " + tablename
        else:
            frameheader = setup['streamTable'][0]['header']

        nvp = \
            [
                ('R_CTL','0x%.2X'%frameheader['RCTL']),
                ('F_CTL','0x%.2X%.2X%.2X'%(frameheader['FCTL'][2], frameheader['FCTL'][1], frameheader['FCTL'][0])),
                ('CS_CTL','0x%.2X'%frameheader['CSCNTL']),
                ('DF_CTL','0x%.2X'%frameheader['DECTL']),
                ('D_ID','0x%.2X%.2X%.2X'%(frameheader['DID'][2], frameheader['DID'][1], frameheader['DID'][0])),
                ('S_ID','0x%.2X%.2X%.2X'%(frameheader['SID'][2], frameheader['SID'][1], frameheader['SID'][0])),
                ('OX_ID','0x%.2X%.2X'%(frameheader['OXID'][1], frameheader['OXID'][0])),
                ('RX_ID','0x%.2X%.2X'%(frameheader['RXID'][1], frameheader['RXID'][0])),
                ('SEQ_ID','0x%.2X'%frameheader['SEQID']),
                ('TYPE','0x%.2X'%frameheader['type']),
                ('SEQ_CNT','0x%.2X%.2X'%(frameheader['SEQCNT'][1], frameheader['SEQCNT'][0])),
                ('PARAMETER','0x%.2X%.2X%.2X%.2X'%(frameheader['parameter'][3], frameheader['parameter'][2], frameheader['parameter'][1], frameheader['parameter'][0]))
            ]

        if format == 'pdf':
            makeTable = self.createPdfTable
            for n,v in nvp:
                table.append([n,v])        
        else:
            makeTable = self.createCsvTable
            for n,v in nvp:
                table.append([n,v])

        makeTable(fd, tablename, table)


    def throughputStreamPayloadFC(self, fd, setup, format, isThroughput = True):
    
        tablename = "Payload Setup"
        
        isThroughputFC1 = False
        if isThroughput:
            layer = setup['testLayer']
            if layer == 'FC_FC2':
                pattern = setup['stream']['pattern']
                table_name = "FC-2 - " + tablename
            else:
                isThroughputFC1 = True
                pattern = setup['FC1_Pattern']
                table_name = "FC-1 - " + tablename
        else:
            pattern = setup['streamTable'][0]['pattern']
            table_name = tablename

        pattern_invert = 'Off'
        if pattern['invert'] != 0: pattern_invert = 'On'
        sunriseTag = get_param(pattern, 'tag')
        if sunriseTag == 'VER1':
            sunriseTag = 'SN/TS'
            self.snts = True
        elif sunriseTag == 'VER2':
            sunriseTag = 'SR-TAG'

        pattern_type = get_param(pattern, 'type')
        ITU_T_O150_Compatible = get_param(pattern, 'ITU_T_O150')
        if ITU_T_O150_Compatible == 'ENABLE':
            ITU_T_O150_Compatible = 'Enable'
        else:
            ITU_T_O150_Compatible = 'Disable'

        nvp = []
        if (not isThroughputFC1) and pattern_type != 'CJPAT' and pattern_type != 'CRPAT':
            nvp.append(('Sunrise Tag', sunriseTag))
        nvp.append(('Pattern Type', pattern_type))

        if pattern_type == 'USER':
            nvp.append(('User Pattern', hex(get_param(pattern, 'userPattern')).rstrip('L').upper()))
        elif pattern_type.startswith('2E'):
            nvp.append(('ITU-T O.150 Compatible', ITU_T_O150_Compatible))
            nvp.append(('Pattern Invert', pattern_invert))

        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n,v in nvp:
                table.append([n,v])
        else:
            makeTable = self.createCsvTable
            for n,v in nvp:
                table.append([n,v])
           
        makeTable(fd,table_name,table)
        
    def throughputStreamTrafficSetupFC(self, fd, setup, format):

        stream_table = setup['stream']
        table_name = "FC-2 - Traffic Setup"
            
        traffic = stream_table['trafficShape']      
    
        traffic_shape = get_param(traffic, 'type')
        traffic_rate = get_param(traffic, 'unitType')

        if traffic_shape == 'CONSTANT':
            traffic_shape_name = 'Constant'
        elif traffic_shape == 'RAMP':
            traffic_shape_name = 'Ramp'
        elif traffic_shape == 'BURST':
            traffic_shape_name = 'Burst'

        if traffic_rate == 'PERCENTAGE':
            traffic_rate_name = 'Percentage'
        elif traffic_rate == 'BITRATE':
            traffic_rate_name = 'Bit Rate'

        nvp = []
        nvp.append( ('Traffic Shape',traffic_shape_name) )
        nvp.append( ('Rate',traffic_rate_name) )

        if traffic_shape == 'CONSTANT':
            if traffic_rate == 'PERCENTAGE':
                name = 'Constant Bandwidth (%)'
                value = "%.2f"%(traffic['constant']['bandwidth']/1000000.0)
            elif traffic_rate == 'BITRATE':
                name = 'Constant Bit Rate (kbps)'
                value = get_param_from_path(traffic, 'constant', 'bitrate')
            nvp.append( (name, value) )
        elif traffic_shape == 'RAMP':
            if traffic_rate == 'PERCENTAGE':
                nvp.append( ('Start Bandwidth (%)',"%.2f"%(traffic['ramp']['startBandwidth']/1000000.0)))
                nvp.append( ('Stop Bandwidth (%)',"%.2f"%(traffic['ramp']['stopBandwidth']/1000000.0)))
                nvp.append( ('Step Bandwidth (%)',"%.2f"%(traffic['ramp']['stepSize']/1000000.0)))
                nvp.append( ('Step Duration (sec)',get_param_from_path(traffic, 'ramp', 'stepDuration')))
            elif traffic_rate == 'BITRATE':
                nvp.append( ('Start Bit Rate (kbps)',get_param_from_path(traffic, 'ramp', 'startbitrate')))
                nvp.append( ('Stop Bit Rate (kbps)',get_param_from_path(traffic, 'ramp', 'stopbitrate')))
                nvp.append( ('Step Bit Rate (kbps)',get_param_from_path(traffic, 'ramp', 'stepbitrate')))
                nvp.append( ('Step Duration (sec)',get_param_from_path(traffic, 'ramp', 'stepDuration')))
        elif traffic_shape == 'BURST':
            if traffic_rate == 'PERCENTAGE':
                nvp.append( ('Burst 1 Bandwidth (%)',"%.2f"%(traffic['burst']['bandwidth1']/1000000.0)) )
                nvp.append( ('Burst 1 Duration (sec)',get_param_from_path(traffic, 'burst', 'duration1')) )
                nvp.append( ('Burst 2 Bandwidth (%)',"%.2f"%(traffic['burst']['bandwidth2']/1000000.0)) )
                nvp.append( ('Burst 2 Duration (sec)',get_param_from_path(traffic, 'burst', 'duration2')) )
            elif traffic_rate == 'BITRATE':
                nvp.append( ('Burst 1 Bit Rate (kbps)',get_param_from_path(traffic, 'burst', 'bitrate1')) )
                nvp.append( ('Burst 1 Duration (sec)',get_param_from_path(traffic, 'burst', 'duration1')) )
                nvp.append( ('Burst 2 Bit Rate (kbps)',get_param_from_path(traffic, 'burst', 'bitrate2')) )
                nvp.append( ('Burst 2 Duration (sec)',get_param_from_path(traffic, 'burst', 'duration2')) )

        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n,v in nvp:
                table.append([n,v])
        else:
            makeTable = self.createCsvTable
            for n,v in nvp:
                table.append([n,v])
           
        makeTable(fd,table_name,table)
   
    def bertSetup(self, fd, config, format):
        try:
            setup = config['config']['ether']['stBertConfig']
        except:
            self.write_log('Throughput setup data not found!', 'Error', sys.exc_info())
            return                       
        
        #Throughput Test Setup       
        self.throughputTestSetup(fd, setup, format)

        test_layer = get_param(setup, 'testLayer')
        if test_layer == 'L1UNFRAME' or test_layer == 'L1FRAME':
            self.throughputStreamTrafficSetup(fd, setup, format, 0, test_layer)
       
        #Throughput Stream Setup         
        if test_layer == 'L2FRAME':
            self.throughputStreamGeneralSetup(fd, setup, format)
                                            
            num_streams = get_param(setup, 'numOfStreams', 0)
            #to Fix bug 16870
            self.show_stream_latency = 1
            '''
            if num_streams == 1:
                self.show_stream_latency = 0
            else:
                self.show_stream_latency = 1
            '''
            
            sno = 0
            while sno < num_streams:
                sno += 1
                streamTable = setup['streamTable'][sno - 1]
                layerConfig = streamTable['layerConf']
                envlan = get_param(layerConfig, 'enVlan')
                enmpls = get_param(layerConfig, 'enMpls')
                strip = get_param(layerConfig, 'layer234Type')
        
                self.throughputStreamMacSetup(fd, streamTable, format, sno)               
                if envlan != 0: 
                    self.throughputStreamVlanSetup(fd, streamTable, format, sno)
                if enmpls != 0:
                    self.throughputStreamMplsSetup(fd, streamTable, format, sno)

                if strip == 'IP' or strip == 'TCP' or strip == 'UDP':
                    self.throughputStreamIpSetup(fd, streamTable, format, sno)

                if strip == 'TCP':
                    self.throughputStreamTcpSetup(fd, streamTable, format, sno)

                if strip == 'UDP':
                    self.throughputStreamUdpSetup(fd, streamTable, format, sno)

                self.throughputStreamTrafficSetup(fd, streamTable, format, sno)
                self.throughputStreamRxFilterSetup(fd, streamTable, format, sno)
        
    def throughputTestSetup(self, fd, setup, format):
        test_type = get_param(setup,'testType')
        if test_type == 'LIVE':
            test_type = 'Live'
        else:
            test_type = 'BERT'
       
        test_layer_code = get_param(setup, 'testLayer')
        try:
            if self.interface == 'XFP':
                test_layer = {'L1UNFRAME': 'Layer 1 64/66B', 'L1FRAME': 'Layer 2 PRBS+FCS', 'L2FRAME': 'Layer 2/3/4'}[test_layer_code]
            elif self.interface == 'SFP':
                test_layer = {'L1UNFRAME': 'Layer 1 8/10B', 'L1FRAME': 'Layer 2 PRBS+FCS', 'L2FRAME': 'Layer 2/3/4'}[test_layer_code]
            elif self.interface == 'RJ45':
                test_layer = {'L1UNFRAME': 'Layer 1 4/5B', 'L1FRAME': 'Layer 2 PRBS+FCS', 'L2FRAME': 'Layer 2/3/4'}[test_layer_code]
            else:
                test_layer = NA
        except:
            test_layer = NA
            self.write_log('Problem setting BERT layer', 'Error', sys.exc_info())
        
        nvp = \
            [ 
                ('Test Type', test_type),
                ('Test Layer', test_layer)
            ]
        
        if test_layer_code == 'L1FRAME':
            try:
                stable = setup['streamTable'][0] # agregate
                nvp.append(('Frame Size', get_param_from_path(stable, 'frameSize', 'constFrameLength')))
            except:
                self.write_log('Stream Table info not found!', 'Error', sys.exc_info())

        if test_layer_code == 'L2FRAME':
            nvp.append(('Total Stream', get_param(setup, 'numOfStreams', 0)))
        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n, v in nvp:
                table.append([n,v])            
        else:
            makeTable = self.createCsvTable
            for n, v in nvp:
                table.append([n,v])                 
            
        makeTable(fd, "Throughput Test Setup", table)
    
    def throughputStreamGeneralSetup(self, fd, setup, format):
        num_streams = get_param(setup, 'numOfStreams', 0)
       
        table = []
        names_inserted = False
            
        stream_tables = setup['streamTable']    
        sno = 0
        while sno < num_streams:
            sno += 1            
            stream_table = stream_tables[sno - 1]
            layerConf = stream_table['layerConf']
            ipHeader = stream_table['ipHeader']
            structure = 'MAC'            

            layer_type = get_param(layerConf, 'layer234Type', False)
            if layer_type == 'IP':
                structure += ' IP '
            elif layer_type == 'TCP':
                structure += ' IP TCP'
            elif layer_type == 'UDP':
                structure += ' IP UDP '

            if get_param(layerConf, 'enMacInMac', False):
                structure += ' MACinMAC ' 
            if get_param(layerConf, 'enVlan', False):
                structure += ' VLAN ' 
            if get_param(layerConf, 'enMpls', False):
                structure += ' MPLS '
            

                
            structure = structure.strip(' ')
            frametype = get_param_from_path(stream_table, 'frameSize', 'frameSizeType')
            framesize = get_param_from_path(stream_table, 'frameSize', 'constFrameLength')
            nvp = \
                [
                    ('Stream No.', sno),
                    ('Structure', structure),
                    ('Frame Type', frametype),
                    ('Frame Size', framesize)
                ]            
            names = []
            values = []
            for n,v in nvp:
                if format == 'pdf':
                    makeTable = self.createPdfTable
                    names.append(n)
                else:
                    makeTable = self.createCsvTable
                    names.append(CSV_NAME(n))
                values.append(v)
               
            if not names_inserted:
                table.append(names)
                names_inserted = True
            
            table.append(values)

        makeTable(fd,"General Stream Setup",table)  

    def throughputStreamMacSetup(self, fd, streamTable, format, sno):
        try:
            setup = streamTable['macFrame']
        except:
            self.write_log('Throughput Stream Mac setup data not found!', 'Error', sys.exc_info())
            return
        
        frame_type = get_param(setup,'macFrameType')
        
        if frame_type == 'IEEE802.3':
            eth_type = 'Length'
        else:
            eth_type = int_to_hex(setup['etherType'], 4, True)

        setup2 = streamTable['layerConf']
        llcendis = 'Disable'
        snapendis = 'Disable'
        strllc =  get_param(setup2,'format802_2')
        if strllc == 'LLC' or strllc == 'SNAP':
            llcendis = 'Enable'

        if strllc == 'SNAP':
            snapendis = 'Enable'

        nvp = \
            [
                ('Frame Type', frame_type),
                ('Ethernet Type', eth_type),
                ('MAC Source', get_param(setup, 'macSrc')),
                ('MAC Destination', get_param(setup, 'macDest')),
                ('LLC', llcendis),
                ('SNAP', snapendis)
            ]
        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n,v in nvp:
                table.append([n,v])        
        else:
            makeTable = self.createCsvTable
            for n,v in nvp:
                table.append([n,v])   
            
        makeTable(fd,"Stream %s - MAC Setup" % sno,table)
        
    def throughputStreamVlanSetup(self, fd, streamTable, format, sno):
        try:
            setup = streamTable['vlan']
        except:
            self.write_log('Throughput Vlan setup data not found!', 'Error', sys.exc_info())
            return        
    
        if format == 'pdf':
            makeTable = self.createPdfTable
        else:
            makeTable = self.createCsvTable

        num_vlans = get_param(streamTable, "nvlan")
        stream_vlan_table = self.getVlanTable(setup, num_vlans)
        makeTable(fd, "Stream %s - VLAN Setup" % sno, stream_vlan_table)
        
    def throughputStreamMplsSetup(self, fd, streamTable, format, sno):
        try:
            setup = streamTable['mplsCfg']
        except:
            self.write_log('Throughput Mpls setup data not found!', 'Error', sys.exc_info())
            return
        
        num_mpls = get_param(streamTable, "nmpls")
            
        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            names = ['Type','ID','Experimental','Bottom of Stack','Time to Live']
        else:
            makeTable = self.createCsvTable
            names = ["Type","ID","Experimental","Bottom of Stack","Time to Live"]
        table.append(names)
        num=0
        for mpls in setup:
            values = \
                [
                    get_param(streamTable, 'mplsUnicast'),
                    hex(get_param(mpls, 'hopLabel', 33024)),
                    get_param(mpls, 'exp'),
                    get_param(mpls, 'eofStack'),
                    get_param(mpls, 'timeToLive')
                ]
            if num < num_mpls:
                table.append(values)
            num=num+1

        makeTable(fd,"Stream %s - MPLS Setup"%sno,table)
        
    def throughputStreamIpSetup(self, fd, streamTable, format, sno):
        try:
            setup = streamTable['ipHeader']
        except:
            self.write_log('Throughput ipHeader setup data not found!', 'Error', sys.exc_info())
            return
        iptos = get_param(setup, 'iptos')
#        iptos = get_param(setup, 'rfctos')

        nvp = \
            [   
                ('Source',get_param(setup,'ipSrc')),
                ('Destination',get_param(setup,'ipDest')),
                ('Default Gateway',get_param(setup,'ipGateway')),
                ('Subnet Mask',get_param(setup, 'subnetMask', '255.255.255.0')),
                ('IP Version',get_param(setup, 'versionAndLength')>>4),
                ('Protocol', get_param(setup, 'protocol')),
                ('Type of Service', iptos)
            ]
        tos = get_param(setup, 'tos')

        if iptos == 'RFC1349':
            precedence = tos>>5
            nvp.append(('Precedence', precedence))
            nvp.append(('Type of Service', hex((tos>>1)&0x0F)))
            nvp.append(('MBZ', tos & 0x01))
        else:
            nvp.append(('DSCP', int_to_hex(tos>>2, 2, True)))
            nvp.append(('Currently Unused', (tos & 0x03)))

        nvp.append(('Header Length',get_param(setup, 'versionAndLength')&0x0F))
        nvp.append(('Identifier', int_to_hex(setup['identifier'], 4, True)))
        
        fragFlagsAndOffset = get_param(setup, 'fragFlagsAndOffset')
        nvp.append(('Flag Don\'t Fragment', (fragFlagsAndOffset>>14)&0x01))
        nvp.append(('Flag More Fragment', (fragFlagsAndOffset>>13)&0x01))
        nvp.append(('Fragment Offset', fragFlagsAndOffset&0x1FFF))
        nvp.append(('Time To Live', get_param(setup, 'timeToLive')))

        # Stream IP Options
        if get_param(setup, 'enipopt') != 0:
            optlen = get_param(setup, 'optlen')
            nvp.append(('Length of IP Option', optlen))
            opt_data = setup['optdata'];
            num = 0
            for opt in opt_data:
                num = num + 1
                nvp.append(('Option Data %d' % num, int_to_hex(opt, 8, True)))
                if num >= optlen:
                    break
        else:
            nvp.append(('IP Option', 'Disable'))

        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n,v in nvp:
                table.append([n,v])
        else:
            makeTable = self.createCsvTable
            for n,v in nvp:
                table.append([n,v])
            
        makeTable(fd,"Stream %s - IP Setup"%sno,table)

    def throughputStreamTcpSetup(self, fd, streamTable, format, sno):
        try:
            setup = streamTable['tcpHeader']
        except:
            self.write_log('Throughput tcpHeader setup data not found!', 'Error', sys.exc_info())
            return
        nvp = \
                [
                    ('Source Port', get_param(setup, 'SrcPort')),
                    ('Destination Port',get_param(setup, 'DestPort')),
                    ('Sequence Number',hex(get_param(setup, 'SeqNum'))),
                    ('ACK Number',hex(get_param(setup, 'AckNum'))),
                    ('Data Offset',altbin((get_param(setup, 'OffsetResFlags')>>12)&0x0F)),
                    ('Reserved 6 bits',altbin((get_param(setup, 'OffsetResFlags')>>6)&0x3F)),
                    ('Window Size',hex(get_param(setup, 'WinSize'))),
                    ('Urgent Pointer',hex(get_param(setup, 'UrgentPtr'))),
                    ('URG',(get_param(setup, 'OffsetResFlags')>>5)&0x01),
                    ('ACK',(get_param(setup, 'OffsetResFlags')>>4)&0x01),
                    ('PSH',(get_param(setup, 'OffsetResFlags')>>3)&0x01),
                    ('RST',(get_param(setup, 'OffsetResFlags')>>2)&0x01),
                    ('SYN',(get_param(setup, 'OffsetResFlags')>>1)&0x01),
                    ('FIN',(get_param(setup, 'OffsetResFlags')&0x01)),
                ]    
        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n,v in nvp:
                table.append([n,v])
        else:
            makeTable = self.createCsvTable
            for n,v in nvp:
                table.append([n,v])

        makeTable(fd,"Stream %s - TCP Setup"%sno,table)            

    def throughputStreamUdpSetup(self, fd, streamTable, format, sno):
        try:
            setup = streamTable['udpHeader']
        except:
            self.write_log('Throughput udpHeader setup data not found!', 'Error', sys.exc_info())
            return
        nvp = \
        [
            ('Source Port', get_param(setup, 'SrcPort')),
            ('Destination Port', get_param(setup, 'DestPort'))
        ]
        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n,v in nvp:
                table.append([n,v])
        else:
            makeTable = self.createCsvTable
            for n,v in nvp:
                table.append([n,v])
        
        makeTable(fd, "Stream %s - UDP Setup" % sno,table)
        
    def throughputStreamTrafficSetup(self, fd, setup, format, sno, layer='L2FRAME'):
        if layer != 'L2FRAME':
            stream_table = setup['streamTable'][sno]
        else:
            stream_table = setup
        
        #if layer == 'L1UNFRAME' and sno == 0:          
        #    table_name = "Layer 1 Unframed - Test Pattern"
        #elif layer == 'L1FRAME' and sno == 0:            
        #    table_name = "Layer 1 Framed - Traffic Setup"
        #else:
        #    table_name = "Stream %s - Traffic Setup" % sno
            
        traffic = stream_table['trafficShape']      
        pattern = stream_table['pattern']
        pattern_invert = 'Off'
        if pattern['invert'] != 0: pattern_invert = 'On'
        sunriseTag = get_param(pattern, 'tag')
        if sunriseTag == 'VER1':
            sunriseTag = 'SN/TS/SR-TAG'
            self.snts = True
        elif sunriseTag == 'VER2':
            sunriseTag = 'STAG'
    
        traffic_threshold = get_param(traffic, 'servDisruptThreshold') * 0.001
        traffic_shape = get_param(traffic, 'type')
        traffic_rate = get_param(traffic, 'unitType')
        pattern_type = get_param(pattern, 'type')
        nv_pattern = \
        [              
            ('Sunrise Tag', sunriseTag),
            ('Pattern Type', pattern_type)
        ]         
                  
        if pattern_type == 'USER':
            nv_pattern.append(('User Pattern Type', 'USER'))
            nv_pattern.append(('User Pattern', hex(get_param(pattern, 'userPattern')).rstrip('L')))
        elif pattern_type == 'USER1024':
            pat_data = pattern['userPattern1024']
            for i in range(1,33):
                nv_pattern.append(('Pattern Data %d' %i, hex(pat_data[i - 1]).rstrip('L')))
        elif pattern_type in ('ALL1', 'ALL0', 'ALT1'):
            pass            
        else:
            nv_pattern.append(('Pattern Invert', pattern_invert))
   
        #if layer == 'L2FRAME':
        #   nvp = \
        #   [            
        #('Frame Type', get_param_from_path(stream_table , 'frameSize', 'frameSizeType')),
        #('Sunrise Tag', sunriseTag),
        #   ]
        #else:
        #   nvp = \
        #   [
        #     #('Frame Type', get_param_from_path(stream_table , 'frameSize', 'frameSizeType')),
        #   ]
        nvp = []
        nvp.append(('Traffic Shape',traffic_shape))
        nvp.append(('Traffic Rate',traffic_rate))
        nvp.append(('Disruption Threshold', traffic_threshold))

        name = None
        if traffic_shape == 'CONSTANT':
            if traffic_rate == 'PERCENTAGE':
                name = 'Constant Bandwidth (%)'
                value = get_param_from_path(traffic, 'constant', 'bandwidth')
                if value != NA:
                    try:
                        value = value * 0.01
                    except: 
                        value = NA
            elif traffic_rate == 'BITRATE':
                name = 'Constant Bit Rate (kbps)'
                value = get_param_from_path(traffic, 'constant', 'bandwidth')
            elif traffic_rate == 'IPG':
                name = 'Constant IPG (ns)'
                value = get_param_from_path(traffic, 'constant', 'bandwidth')
            if name is not None:
                nvp.append((name, value))
        
        elif traffic_shape == 'RAMP':
            if traffic_rate == 'PERCENTAGE':
                name = 'Start Bandwidth (%)'
                value = get_param_from_path(traffic, 'ramp', 'startBandwidth')
                if value != NA:
                    try:
                        value = value * 0.01
                    except: 
                        value = NA
                nvp.append((name, value))
                name = 'Stop Bandwidth (%)'
                value = get_param_from_path(traffic, 'ramp', 'stopBandwidth')
                if value != NA:
                    try:
                        value = value * 0.01
                    except: 
                        value = NA
                nvp.append((name, value))
                name = 'Step Bandwidth (%)'
                value = get_param_from_path(traffic, 'ramp', 'stepSize')
                if value != NA:
                    try:
                        value = value * 0.01
                    except: 
                        value = NA
                nvp.append((name, value))
                name = 'Step Duration (sec)'
                value = get_param_from_path(traffic, 'ramp', 'stepDuration')
                nvp.append((name, value))
            elif traffic_rate == 'BITRATE':
                nvp.append( ('Start Bit Rate (kbps)',get_param_from_path(traffic, 'ramp', 'startBandwidth')))
                nvp.append( ('Stop Bit Rate (kbps)',get_param_from_path(traffic, 'ramp', 'stopBandwidth')))
                nvp.append( ('Step Bit Rate (kbps)',get_param_from_path(traffic, 'ramp', 'stepSize')))
                nvp.append( ('Step Duration (sec)',get_param_from_path(traffic, 'ramp', 'stepDuration')))
            elif traffic_rate == 'IPG':
                nvp.append( ('Start IPG (ns)',get_param_from_path(traffic, 'ramp', 'startBandwidth')))
                nvp.append( ('Stop IPG (ns)',get_param_from_path(traffic, 'ramp', 'stopBandwidth')))
                nvp.append( ('Step IPG (ns)',get_param_from_path(traffic, 'ramp', 'stepSize')))
                nvp.append( ('Step Duration (sec)',get_param_from_path(traffic, 'ramp', 'stepDuration')))
        elif traffic_shape == 'BURST':
            if traffic_rate == 'PERCENTAGE':
                name = 'Burst #1 Bandwidth (%)'
                value = get_param_from_path(traffic, 'burst', 'bandwidth1')
                if value != NA:
                    try:
                        value = value * 0.01
                    except: 
                        value = NA
                nvp.append((name, value))
                nvp.append( ('Burst #1 Duration (sec)',get_param_from_path(traffic, 'burst', 'duration1')))
                name = 'Burst #2 Bandwidth (%)'
                value = get_param_from_path(traffic, 'burst', 'bandwidth2')
                if value != NA:
                    try:
                        value = value * 0.01
                    except: 
                        value = NA
                nvp.append((name, value))
                nvp.append( ('Burst #2 Duration (sec)',get_param_from_path(traffic, 'burst', 'duration2')))
            elif traffic_rate == 'BITRATE':
                nvp.append( ('Burst #1 Bit Rate (kbps)',get_param_from_path(traffic, 'burst', 'bandwidth1')))
                nvp.append( ('Burst #1 Duration (sec)',get_param_from_path(traffic, 'burst', 'duration1')))
                nvp.append( ('Burst #2 Bit Rate (kbps)',get_param_from_path(traffic, 'burst', 'bandwidth2')))
                nvp.append( ('Burst #2 Duration (sec)',get_param_from_path(traffic, 'burst', 'duration2')))
            elif traffic_rate == 'IPG':          
                nvp.append( ('Burst #1 IPG (ns)',get_param_from_path(traffic, 'burst', 'bandwidth1')))
                nvp.append( ('Burst #1 Duration (sec)',get_param_from_path(traffic, 'burst', 'duration1')))
                nvp.append( ('Burst #2 IPG (ns)',get_param_from_path(traffic, 'burst', 'bandwidth2')))
                nvp.append( ('Burst #2 Duration (sec)',get_param_from_path(traffic, 'burst', 'duration2')))
    
        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n,v in nv_pattern:
                table.append([n,v])
        else:
            makeTable = self.createCsvTable
            for n,v in nv_pattern:
                table.append([n,v])
        if  layer == 'L1UNFRAME' and sno == 0:
            makeTable(fd, "Layer 1 Unframed - Test Pattern", table)
            return
        elif layer == 'L1FRAME' and sno == 0:           
            makeTable(fd, "Layer 2 PRBS+FCS Test Pattern", table)
        else:
            makeTable(fd, "Stream %s - Test Pattern/Payload" % sno, table)
                     
        table = []  
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n,v in nvp:
                table.append([n,v])
        else:
            makeTable = self.createCsvTable
            for n,v in nvp:
                table.append([n,v])
        if  layer == 'L1FRAME' and sno == 0:
            makeTable(fd, "Layer 2 PRBS+FCS Traffic Shape", table)
        else:
            makeTable(fd, "Stream %s - Traffic Setup" % sno, table)

    def throughputStreamRxFilterSetup(self, fd, setup, format, sno):       
        nvp = \
            [
                ('MAC Source',get_param(setup['dontCare'], 'macSrc', ENDI)),
                ('MAC Destination',get_param(setup['dontCare'], 'macDst', ENDI)),
                ('IP Source',get_param(setup['dontCare'], 'ipSrc',ENDI)),
                ('IP Destination',get_param(setup['dontCare'], 'ipDst',ENDI)),
                #('VLAN #1',get_param(setup, 'envlanid1')),
                #('VLAN #2',get_param(setup, 'envlanid2')),
                #('VLAN #3',get_param(setup, 'envlanid3'))
            ]

        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n,v in nvp:
                table.append([n,v])
        else:
            makeTable = self.createCsvTable
            for n,v in nvp:
                table.append([n,v])
           
        makeTable(fd, "Stream %s - Rx Filter Setup" % sno, table)

    def systemInfoTable(self, fd, systemInfo, format):
        try:
            setup = systemInfo['moduleinfo']['moduleinfo']
            #print 'ModuleInfo = ', setup
        except:
            self.write_log('System Info data not found!', 'Error', sys.exc_info())
            return

        systemInfo_table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            colwidths = [1.7625 * inch, 1.7625 * inch, 1.7625 * inch, 1.7625 * inch]
            systemInfo_table.append(['RxT-TEN Test Set Information', '', '', ''])
        else:
            makeTable = self.createCsvTable
            colwidths = None
            systemInfo_table.append(["RxT-TEN Test Set Information", "", "", ""])
        setInfo = \
        (
            ['System Version', setup['systemVersion'], 'System Serial No', setup['systemSerialNo']],
            ['Module Version', setup['moduleVersion'], 'Module Serial No', setup['serialNumber']],
            ['Calibration', '', 'Due Date', ''],
        )
        systemInfo_table.extend(setInfo)
        if  setup.has_key('gpsoption') and setup['gpsoption']:
            systemInfo_table.append(['Longitude', setup['gpslongitude'], 'Latitude', setup['gpslatitude']])
        else:
            systemInfo_table.append(['Longitude', 'N/A', 'Latitude', 'N/A'])

        systemInfo_table.append(['Measurement', '', '', ''])
        systemInfo_table.append(['Start', self.testStart, 'Stop', self.testStop])
        systemInfo_table.append(['Report Name', self.report_file_name, '', ''])

        style = \
            [   
                ('BOX', (0, 0), (-1, 0), 1, colors.grey),
                ('BOX', (0, 5), (-1, 5), 1, colors.grey),
                ('BOX', (0, 7), (-1, 7), 1, colors.grey),
                ('BOX', (1, 1), (1, -1), 1, colors.grey),
                ('BOX', (2, 1), (2, -1), 1, colors.grey),
                ('SPAN', (0, 5), (-1, 5)),
                ('SPAN', (1, 7), (-1, 7)),
                ('SPAN', (0, 0), (-1, 0)),
            ]

        makeTable(fd, "System Information", systemInfo_table, style, colwidths)

    def customerData(self, fd, format):
        colsize = 2.325
        customer_table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            colwidths = [1.2 * inch, colsize * inch, 1.2 * inch, colsize * inch]
            customer_table.append(['Customer Information', '', '', ''])
        else:
            makeTable = self.createCsvTable
            colwidths = None
            customer_table.append(["Customer Information", "", "", ""])

        custInfo = \
        (
            ['Name', self.wrap1Text(self.report_info['custname'], colsize), 'Contact Name', self.wrap1Text(self.report_info['contactname'], colsize)],
            ['Phone', self.wrap1Text(self.report_info['custphone'], colsize), 'Email', self.wrap1Text(self.report_info['custemail'], colsize)],
            ['Address', self.wrap1Text(self.report_info['custaddress'], 5.85), '', ''],
        )

        customer_table.extend(custInfo)
        customer_table.append(['User Information', '', '', ''])

        userInfo = \
        (
            ['Name', self.wrap1Text(self.report_info['username'], colsize), 'Title', self.wrap1Text(self.report_info['title'], colsize)],
            ['Phone', self.wrap1Text(self.report_info['userphone'], colsize), 'Email', self.wrap1Text(self.report_info['useremail'], colsize)],
            ['Address', self.wrap1Text(self.report_info['useraddress'], 5.85), '', ''],
        )

        customer_table.extend(userInfo)

        style = \
            [   
                ('BOX', (0, 0), (-1, -1), 1, colors.grey),
                ('BOX', (0, 0), (-1, 0), 1, colors.grey),
                ('BOX', (1, 3), (-1, 3), 1, colors.grey),
                ('BOX', (0, 4), (-1, 4), 1, colors.grey),
                ('BOX', (1, 1), (1, -1), 1, colors.grey),
                ('BOX', (2, 1), (2, -1), 1, colors.grey),
                ('BOX', (1, 5), (-1, 6), 1, colors.grey),
                ('SPAN', (0, 0), (-1, 0)),
                ('SPAN', (1, 3), (-1, 3)),
                ('SPAN', (0, 4), (-1, 4)),
                ('SPAN', (1, 7), (-1, 7)),
            ]

        makeTable(fd, 'User Information', customer_table, style, colwidths)

    def wrap1Text(self, text, size):
        #mtl = 400
        mtl = size * 72 * 0.85 #85% # 1 inch is 72 point
        res2 = ''
        
        while self.dataFont.stringWidth(text, dataFontSize) > mtl:
            pos = 0
            line = ''
            while self.dataFont.stringWidth(line, dataFontSize) <= mtl:
                line += text[pos]
                pos += 1               
            res2 += line + '\n'
            text = text[pos:]
        res2 += text
        return res2

    def wrapText(self, name, text, size):
        #mtl = 400
        mtl = size * 72 * 0.85 #85% # 1 inch is 72 point
        res = ''
        res2 = ''
        
        while self.dataFont.stringWidth(text, dataFontSize) > mtl:
            pos = 0
            line = ''
            while self.dataFont.stringWidth(line, dataFontSize) <= mtl:
                line += text[pos]
                pos += 1               
            res2 += line + '\n'
            #name += '\n'
            text = text[pos:]
        res2 += text
        #res += name
        return name, res2

    def comments(self, fd, format):
        col_size = 5.85
        nvp = \
            [
                (self.wrapText('Ticket ID', self.report_info['ticketid'], col_size)),
                (self.wrapText('Note', self.report_info['note'], col_size)),
                (self.wrapText('Comment 1', self.report_info['comment1'], col_size)),
                (self.wrapText('Comment 2', self.report_info['comment2'], col_size)),
                (self.wrapText('Comment 3', self.report_info['comment3'], col_size)),
            ]

        if format == 'pdf':
            makeTable = self.createPdfTable
            style = []
            colwidths = [1.2 * inch, col_size * inch]
        else:
            makeTable = self.createCsvTable
            style = []
            colwidths = None
        makeTable(fd, 'Comments', nvp, style, colwidths)

    def measSetupFC(self, fd, config, format):
        try:
            setup = config['config']['meas_config']
        except:
            self.write_log('Meas setup data not found!', 'Error', sys.exc_info())
            return

        nvp = []

        stmode = get_param(setup, 'stmode')
        if stmode == 'PROGRAM':
            stmode = 'Program'
            nvp.append(('Start Mode', stmode))
            start_date = get_param(setup, 'stdate')
            start_time = get_param(setup, 'sttime')
            start_time = start_time.replace("_",":")
            nvp.append(('Start Date', start_date))
            nvp.append(('Start Time', start_time))
        elif stmode == 'MANUAL':
            stmode = 'Manual'
            nvp.append(('Start Mode', stmode))

        stpmode = get_param(setup, 'stpmode')
        if stpmode == 'CONTINUOUS':
            stpmode = 'Continuous'
            nvp.append(('Stop Mode', stpmode))    
        elif stpmode == 'TIMED':
            stpmode = 'Timed'
            nvp.append(('Stop Mode', stpmode))            
            dhour = get_param(setup, 'dhour')
            dmin = get_param(setup, 'dmin')
            nvp.append(('Test Hour', dhour))
            nvp.append(('Test Minutes', dmin))

        savemode = {'MANUAL': 'Manual Save',
                    'NEVER': 'Never Save',
                    'AUTO': 'Auto Save',
                   }[get_param(setup, 'savemode')]
        nvp.append(('Save Mode', savemode))

        if self.test_mode == 'FC_BERT':
            bertConfig = config['config']['ether']['stFCBertConfig']
            test_layer = get_param(bertConfig, 'testLayer')
            if test_layer == 'FC_FC2':
                txst = 'Disable'
                if(get_param(setup, 'txcoupled') == 'ON'):
                   txst = 'Enable'
                nvp.append(('Start Tx Coupled', txst))
        
        meas_config_table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n, v in nvp:
                meas_config_table.append([n, v])
        elif format == 'csv':
            makeTable = self.createCsvTable
            meas_config_table = nvp
        
        makeTable(fd, 'Measurement Setup', meas_config_table)
        
    def measSetup(self, fd, config, format):
        try:
            setup = config['config']['meas_config']
        except:
            self.write_log('Meas setup data not found!', 'Error', sys.exc_info())
            return
            
        nvp = []

        stmode = get_param(setup, 'stmode')
        if stmode == 'PROGRAM':
            stmode = 'Program'
            nvp.append(('Start Mode', stmode))
            start_date = get_param(setup, 'stdate')
            start_time = get_param(setup, 'sttime')
            start_time = start_time.replace("-", ":")
            nvp.append(('Start Date', start_date))
            nvp.append(('Start Time', start_time))
        elif stmode == 'MANUAL':
            stmode = 'Manual'
            nvp.append(('Start Mode', stmode))

        stpmode = get_param(setup, 'stpmode')
        if stpmode == 'CONTINUOUS':
            stpmode = 'Continuous'
            nvp.append(('Stop Mode', stpmode))    
        elif stpmode == 'TIMED':
            stpmode = 'Timed'
            nvp.append(('Stop Mode', stpmode))            
            dhour = get_param(setup, 'dhour')
            dmin = get_param(setup, 'dmin')
            nvp.append(('Test Hour', dhour))
            nvp.append(('Test Minutes', dmin))

        savemode = {'MANUAL': 'Manual Save',
                    'NEVER': 'Never Save',
                    'AUTO': 'Auto Save',
                   }[get_param(setup, 'savemode')]
        nvp.append(('Save Mode', savemode))
        
        if self.test_mode == 'THROUGHPUT':
            if(get_param(setup, 'txcoupled') == 'ON'):
                txst = 'Enable'
            else:
                txst = 'Disable'
            nvp.append(('Start Tx Coupled', txst))
        
        #meas_config_table = []
        style = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            colwidths = [3.525 * inch, 3.525 * inch]
            #for n, v in nvp:
            #    meas_config_table.append([n, v])
        elif format == 'csv':
            makeTable = self.createCsvTable
            colwidths = None
            #meas_config_table = nvp
        
        makeTable(fd, 'Measurement Setup', nvp, style, colwidths)

    def sdhMeasParam(self, fd, config, format):
        try:
            setup = config['config']
        except:
            self.write_log('Meas param data not found!', 'Error', sys.exc_info())
            return
        
        refclockVal     = [('INT', 'Internal'),('EXT', 'External')]
        msreiVal        = [('M1_ONLY', 'M1 Only'),('M0_M1', 'M0 and M1')]
        extclkVal       = [('2M_CLOCK', '2M Clock'),
                           ('2M_DATA', '2M Data'),
                           ('1P5_DATA', '1.5M Data'),
                           ('64K_CLOCK','64K + 8K Clock'),
                           ('10M_CLOCK', '10M Clock')]
        #pdb.set_trace()        
        clockType = setup['RefClockType']
        for n,v in refclockVal:
            if n == clockType:
                clockType = v
                
        standard = setup['rx_standard']
        if(standard == 'SONET'):
            ExtClockType = setup['SonetExtClockType']
        else:
            ExtClockType = setup['SdhExtClockType']
        for n,v in extclkVal:
            if n == ExtClockType:
                ExtClockType = v
        
        sdhf = setup['sdhf']
        
        if sdhf.has_key('sd_gate_time'):
            testWindow = str(sdhf['sd_gate_time']) + 'ms'
        else:
            return
            
        msrei = sdhf['M0M1Count']
        for n,v in msreiVal:
            if n == msrei:
                msrei = v
        enhancedRdi = sdhf['enhancedRDI']
        if (enhancedRdi.startswith('EN')):
            enhanceRdi = 'Enable'
        else:
            enhanceRdi = 'Disable'
            
        if(standard == 'SONET'):
            rei_lable = "REI-L Count (OC-192)"
        else:
            rei_lable = "MS-REI Count (STM-64)"
        nvp = \
            [
                ('Frequency Reference Clock', ''),
                ('Clock Type', clockType),
                ('Service Disruption', ''),
                ('Test Window', testWindow),
                ('Others', ''),
                (rei_lable, msrei),
                ('Enhanced RDI', enhanceRdi),
                ('External Clock Type', ExtClockType)
            ]
        style= \
                [
                ('ALIGN', (0, 0),(-1,0),'LEFT'),
                ('ALIGN', (0, 2), (-1, 2),'LEFT'),
                ('ALIGN', (0, 4), (-1, 4),'LEFT'),
                ('BOX', (0, 0), (-1, 0), 1, colors.grey),
                ('BOX', (0, 2), (-1, 2), 1, colors.grey),
                ('BOX', (0, 4), (-1, 4), 1, colors.grey),
                ('SPAN',(0,0),(1,0)),
                ('SPAN',(0,2),(1,2)),
                ('SPAN',(0,4),(1,4)),
                ]
        if(standard == 'SDH'):
            m21xx_para = sdhf["m21xx_para"]
            m2101 = m21xx_para["m2101"]
            m2110 = m21xx_para["m2110"]
            def getMM(index):
                mm_dict = {
                    1:'1 Minute',
                    15:'15 Minutes',
                    120:'2 Hours',
                    1440:'24 Hours',
                    10080:'7 Days'
                }
                if index in mm_dict:
                    return mm_dict[index]
                #default value is 15 minutes    
                return '15 Minutes'
                
            measure_minutes = getMM(m21xx_para["measure_minutes"])
            hrpvalue = 0.0 +m21xx_para["hrp"] 
            hrp ="%.1f "%(hrpvalue/10)+"%"
            nvp.append(("M.21xx Parameters",""))
            nvp.append(("M.2101",m2101))
            nvp.append(("M.2110",m2110))
            nvp.append(("Meas.Period",measure_minutes))
            nvp.append(("HRP Model",hrp))
            style=\
                [
                ('ALIGN', (0, 0),(-1,0),'LEFT'),
                ('ALIGN', (0, 2), (-1, 2),'LEFT'),
                ('ALIGN', (0, 4), (-1, 4),'LEFT'),
                ('BOX', (0, 0), (-1, 0), 1, colors.grey),
                ('BOX', (0, 2), (-1, 2), 1, colors.grey),
                ('BOX', (0, 4), (-1, 4), 1, colors.grey),
                ('BOX', (0, 8), (-1, 8), 1, colors.grey),
                ('SPAN',(0,0),(1,0)),
                ('SPAN',(0,2),(1,2)),
                ('SPAN',(0,4),(1,4)),
                ('SPAN',(0,8),(1,8)),
                ]
            
        
        meas_config_table = nvp
        if format == 'pdf':
            colwidths = [3.525 * inch, 3.525 * inch]
            makeTable = self.createPdfTable
        elif format == 'csv':
            colwidths = None
            makeTable = self.createCsvTable
        
        #print "Measurement Parameter = ", meas_config_table
        makeTable(fd, 'Measurement Parameters', meas_config_table, style, colwidths)
        
    def sdhPortSetup(self, fd, config, format):
        try:
            profile = config['config']
        except:
            self.log_error('Ports setup data not found!')
            return
            
        #txclk
        rx_standard = profile['rx_standard']
        interface = get_param(profile, 'rx_port_interface')      
        if rx_standard == "SONET":
            setup = profile['sonet']
        else:
            setup = profile['stm']
            
        rxSetup = setup['rx']
        interfaceType = get_param(rxSetup, 'linetype')
        
        txSetup = setup['tx']
        if profile['mode'] == 'LINETHRU' or profile['mode'] == 'PAYLOADTHRU':
            txClockSource = self.getClockLabel('LOOP')
        else:
            txClockSource = self.getClockLabel(get_param(txSetup, 'txclk'))

        linerate = profile['rx_line_rate']
        nw = 0
        if rx_standard == "SONET":
            nw = 1
        linerateStatus = self.getLineRateLabel(linerate, nw)

        ports_config = []
        
        nvp = \
            [
                ('Test Port',interface),
                ('Interface Type',interfaceType),                    
                ('Rate',linerateStatus),
                ('Tx Clock Source', txClockSource),
            ]              

        if format == 'pdf':
            style = []
            colwidths = [3.525 * inch, 3.525 * inch]
            makeTable = self.createPdfTable
        elif format == 'csv':
            colwidths = None
            style = []
            makeTable = self.createCsvTable 
            
        makeTable(fd, 'Port Setup', nvp, style, colwidths)    
    
    def isLP(self, meas_data):
        config = meas_data['config']['config']
        standard = config['rx_standard']
        if(standard == 'SONET'):
            tuvt = config['sonet']['rx']['mapping']
        else:
            tuvt = config['stm']['rx']['mapping']
        payload = tuvt['payload']
        austs = tuvt['austs']
        
        if tuvt == 'NONE':
            return False
        else:
            if ((austs == "AU4" and payload.find("VC3") != -1) or
                (payload.find("VC1") != -1) or (payload.find("VT") != -1)):
                return True
            else:
                return False
            
    def isTU3(self, meas_data):
        config = meas_data['config']['config']
        standard = config['rx_standard']
        if(standard == 'SONET'):
            return False
        else:
            mapping = config['stm']['rx']['mapping']
        
        if (mapping['tuvt'] == "TU3"):
            return True
        else:
            return False
    
    def getNwStandard(self, meas_data):
        config = meas_data['config']
        NW_SDH = 0
        NW_SONET = 1
        standardDesc = config['config']['rx_standard']
        if (standardDesc == 'SDH'):
            return NW_SDH
        else:
            return NW_SONET
     
    def getLineRate(self, linerate, nw):
        SDHRATE = [
        ("STM64", "OC192"),
        ("STM16", "OC48"),
        ("STM4", "OC12"),
        ("STM1", "OC3"),
        ("STM0", "STS1")
        ]
        
        i = 0
        while (i < len(SDHRATE)):
            if(SDHRATE[i][0] == linerate or SDHRATE[i][1] == linerate):
                break;
            i += 1
            
        return i
    
    def getLineRateLabel(self, linerate, nw):
        RATE_LBL = [
        ("10G", "OC-192"),
        ("2.5G", "OC-48"),
        ("622M", "OC-12"),
        ("155M", "OC-3"),
        ("52M", "STS-1"),
        ]
        
        return RATE_LBL[self.getLineRate(linerate, nw)][nw]
         
    def getClockLabel(self, clock):
        CLOCK_LBL = [
        ("INT", "Internal"),
        ("EXT", "External"),
        ("LOOP", "Received"),
        ("OFFSET", "Offset"),
        ("DOTS", "DOTS"),
        ("DROP", "DROP"),
        ("BITS", "BITS"),
        ("N/A", "Unknown")
        ]
        i = 0
        while (i < (len(CLOCK_LBL)-1)):
            if(CLOCK_LBL[i][0] == clock):
                break;
            i += 1
            
        return CLOCK_LBL[i][1]
    
    def getSTxAlmErrID(self, str, type):
        SDH_ALARMS = [
            'DEFFECT',
            'LOS',
            'LOF',
            'OOF',
            'RS_TIM',
            'MS_AIS',
            'MS_RDI',
            'AU_LOP',
            'AU_AIS',
            'HP_RDI',
            'HP_SRDI',
            'HP_CRDI',
            'HP_PRDI',
            'HP_TIM',
            'HP_PLM',
            'HP_UNEQ',
            'TU_LOM',
            'TU_LOP',
            'TU_AIS',
            'LP_RFI',
            'LP_RDI',
            'LP_SRDI',
            'LP_CRDI',
            'LP_PRDI',
            'LP_TIM',
            'LP_PLM',
            'LP_EPLM',
            'LP_ELOM',
            'LP_UNEQ',
            'HP_TCUNEQ',
            'HP_TCLTC',
            'HP_TCAIS',
            'HP_TCRDI',
            'HP_TCODI',
            'LP_TCUNEQ',
            'LP_TCLTC',
            'LP_TCAIS',
            'LP_TCRDI',
            'LP_TCODI',
            '10G_LOS',
            '10G_LOF',
            '10G_OOF',
            '10G_MSAIS',
            '10G_MSRDI',
            'LORC',
        ]
        
        SDH_ERRORS = [
            'B1',
            'B2',
            'B3',
            'MS_REI',
            'HP_REI',
            'LP_BIP',
            'LP_REI',
            'AU_PPJ',
            'AU_NPJ',
            'TU_PPJ',
            'TU_NPJ',
            'AU_NDF',
            'TU_NDF',
            'FASE',
            'CODE',
            'HP_TCIEC',
            'HP_TCREI',
            'HP_TCOEI',
            'LP_TCIEC',
            'LP_TCREI',
            'LP_TCOEI'
            ]
        
        id = 0
        try:
            if type == 'alarm':
                id = SDH_ALARMS.index(str.replace('-', '_'))
            else:
                id = SDH_ERRORS.index(str.replace('-', '_'))
        except:
            self.write_log("Error getSTxAlmErrID type=%s, str=%s"%(type, str))
        return id
        
    def getBertAlmErrID(self, str, type):
        BERT_ALARMS = [
            'DEFFECT',
            'LOPS',
            'IS_MATCH',
        ]
        
        BERT_ERRORS = ['BIT' ]
        
        id = 0
        try:
            if type == 'alarm':
                id = BERT_ALARMS.index(str.replace('-', '_'))
            else:
                id = BERT_ERRORS.index(str.replace('-', '_'))
        except:
            self.write_log("Error getBertAlmErrID type=%s, str=%s"%(type, str))
        return id

    def sdhInterfaceSetup(self, fd, config, format):
        
        try:
            setup = config['config']
        except:
            self.log_error('Interface setup data not found!')
            return
            
        tx_standard = setup['tx_standard']
        rx_standard = setup['rx_standard']
        tx_lineRate = setup['tx_line_rate']
        rx_lineRate = setup['rx_line_rate']
        tx_application = setup['tx_application']
        rx_application = setup['rx_application']
                
        testModeCode = setup['mode'];
        testModeName = self.getTestmodeLabel(testModeCode)
            
        txrxCoupled = setup['couple']
        if rx_standard == 'SONET':
            berttype = setup['sonet']['bert']['rx_pattern']['mode']
        else:
            berttype = setup['stm']['bert']['rx_pattern']['mode']
        interface_config = []
        
        nvp = \
            [
                ('Tx Standard',tx_standard),
                ('Rx Standard',rx_standard),                    
                ('Test Mode',testModeName),
                ('Measurement', berttype),
                #('Tx/Rx Coupled', txrxCoupled),
            ]              

        if format == 'pdf':
            style = []
            makeTable = self.createPdfTable
            colwidths = [3.525 * inch, 3.525 * inch]

        elif format == 'csv':
            colwidths = None
            style = []
            makeTable = self.createCsvTable 
            
        makeTable(fd, 'Interface Setup', nvp, style, colwidths)    

    def summaryTableSdh(self, fd, params, format):
        """Writes Measurement Summary Information
           @type  fd: report object
           @param params: 'JSONObject'
           @param format: 'pdf' or 'csv'
        """    
        nw = 0;
        setup = params['config']['config']
        linerate = setup['rx_line_rate']
        rx_standard = setup['rx_standard']
        
        nw_standard = rx_standard
        if nw_standard == "SONET":
            nw = 1
        linerateStatus = self.getLineRateLabel(linerate, nw)
        linerateStatus = nw_standard + " " + linerateStatus + " Status"
        
        results = params['result_sdh']['result']
        if results is None:
            self.log_error("No summary Table Data!")
            self.report_status == 'FAIL'
            return None        
        
        rxpwrbm = str(get_param(results['transceiverInfo'], 'rxpwrbm')) + ' dBm'
        freq = get_param(results['frequency'], 'freq', ICNA) + ' Hz'
        viewType = rx_standard
        
        alarms = results['alarm_seconds']
        isAlarm = False
        errors = results['errors']
        isError = False
        startptrid = self.getSTxAlmErrID('AU_PPJ', 'error')
        endptrid = self.getSTxAlmErrID('TU_NDF', 'error')
        err_id = 0;
        for error in errors:
            if (err_id < startptrid or err_id > endptrid) and error > 0: 
                isError = True
                break
            err_id += 1
            
        for alarm in alarms:
            if alarm > 0: 
                isAlarm = True
                break
            
        # check bert alarm and error
        if isAlarm == False and isError == False:
            bert = results['bert']
            if bert['alarm_seconds'][self.getBertAlmErrID('LOPS', 'alarm')] > 0:
                isAlarm = True
            if bert['errors'][self.getBertAlmErrID('BIT', 'error')] > 0:
                isError = True
        
        if isAlarm == True or isError == True:
            showErrors = 'Errors/Alarms'
            color = colors.red
        else:
            showErrors = 'No Errors'
            color = colors.lightgreen

        etime = setDDHHMMSS(results['common']['elapsedTime'])
        if results['common']['remainingTime'] >= 0:
            rtime = setDDHHMMSS(results['common']['remainingTime'])
        else:
            rtime = 'Continuous'
        nvpq = \
            [                
                ('Elapsed Time', etime),
                ('Remaining Time', rtime),
                ('Signal power', rxpwrbm),
                ('Frequency', freq),
                (viewType, showErrors)
            ]
        
        summary_table = nvpq
        if format == 'pdf':
            style = []
            style.append(('BACKGROUND', (0, 0), (-1, 0), Color(.92, .92, .92)))
            style.append(('BACKGROUND', (0, 2), (-1, 2), Color(.92, .92, .92)))
            style.append(('BACKGROUND', (0, 4), (0, 4), Color(.92, .92, .92)))
            style.append(('BACKGROUND', (1, 4), (1, 4), color))
            colwidths = [3.525 * inch, 3.525 * inch]
            makeTable = self.createPdfTable
        else:
            style = []
            colwidths = None
            makeTable = self.createCsvTable
            
        summaryTableName = "Summary Data " + ': '+ linerateStatus 
        makeTable(fd, summaryTableName, summary_table, style, colwidths)        

    def signalTable(self, fd, results, format):
        """Writes Measurement Summary Information
           @type  fd: report object
           @param params: 'JSONObject'
           @param format: 'pdf' or 'csv'
        """      
        
        rxpwruw = str(fmt_float(results['transceiverInfo']['rxpwruw'], True)) + ' uw'  
        #Paragraph('&#181;w', styleSheet['Normal']).getPlainText()
        rxpwrbm = str(fmt_float(results['transceiverInfo']['rxpwrbm'], True))
        waveLength = str(get_param(results['transceiverInfo'], 'wavelength', ICNA))
        vendor_name = str(get_param(results['transceiverInfo'], 'vendor_name'))
        freq = str(get_param(results['frequency'], 'freq', ICNA))
        freq_offset = str(fmt_float3(results['frequency']['freq_offset'], True))
        min_offset =  str(fmt_float3(results['frequency']['min_offset'], True))
        max_offset =  str(fmt_float3(results['frequency']['max_offset'], True))
        
        signal_table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            colwidths = [1.7625 * inch, 1.7625 * inch, 1.7625 * inch, 1.7625 * inch]
            signal_table.append([Paragraph('<font name = Helvetica size = 10><b>Signal</b></font>', styleSheet['Normal']), '', Paragraph('<font name = Helvetica size = 10><b>Frequency</b></font>', styleSheet['Normal']), ''])
        else:
            makeTable = self.createCsvTable
            colwidths = None
            signal_table.append(["Signal", "", "Frequency", ""])

        setSignal = \
        (
            ['Vendor', vendor_name, 'Frequency', freq + ' Hz'],
            ['wavelength', waveLength + ' nm', 'Freq. Offset', freq_offset + ' ppm'],
            ['RX Power', rxpwruw, 'Min NEG. Offset', min_offset + ' ppm'],
            ['RX Power', rxpwrbm + ' dBm', 'Max POS. Offset', max_offset + ' ppm']
        )
        signal_table.extend(setSignal)
        
        if results['loss_of_reference_clock']==0 and results['frequency']['refclk_is_ext'] :
            clockSlip = \
            (
                ['', '', 'Clock Slips', curtostr(results['frequency']['clock_slip'])],
                ['', '', 'Wander +', curtostr(results['frequency']['pos_wander'])],
                ['', '', 'Wander -', curtostr(results['frequency']['neg_wander'])],
            )
            signal_table.extend(clockSlip)

        style = \
            [   
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, 0), 1, colors.grey),
                ('BOX', (0, 0), (1, -1), 1, colors.grey),
                ('BOX', (2, 0), (2, -1), 1, colors.grey),
                ('SPAN', (0, 0), (1, 0)),
                ('SPAN', (2, 0), (3, 0)),
            ]

        makeTable(fd, "Signal", signal_table, style, colwidths)
        
    def sdhTable(self, fd, results, nw_standard, isLP, isTU3, format):
        
        nw = nw_standard
        RS_LBL = \
            [
                ("LOS", "LOS"),
                ("LOF", "LOF"),
                ("OOF", "OOF"),
                ("RS-TIM", "TIM-S"),
                ("B1", "B1/CV-S"),
                ("FASE", "FASE"),
            ]
        RS_HDR = ["RS", "SECTION"]
            
        tableTitle = RS_HDR[nw]
        self.sdhIndivTable(fd, results, RS_LBL, tableTitle, nw, format)

        MS_HDR = ["MS", "LINE"]
        MS_LBL = [
                  ("MS-AIS", "AIS-L"),
                  ("MS-RDI", "RDI-L"),
                  ("B2", "B2/CV-L"),
                  ("MS-REI", "REI-L")
        ]
    
        tableTitle = MS_HDR[nw]
        self.sdhIndivTable(fd, results, MS_LBL, tableTitle, nw, format)

        
        HP_HDR = ["HP", "PATH"]
        if results['common']['enhancedRDI'] == 'DISABLE':
            HP_LBL = [
                      ("AU-AIS", "AIS-P"),
                      ("AU-LOP", "LOP-P"),
                      ("HP-TIM", "TIM-P"),
                      ("HP-RDI", "RDI-P"),
                      ("HP-PLM", "PLM-P"),
                      ("HP-UNEQ", "UNEQ-P"),
                      ("B3", "B3/CV-P"),
                      ("HP-REI", "REI-P"),
                      ]
        else:
            HP_LBL = [
                      ("AU-AIS", "AIS-P"),
                      ("AU-LOP", "LOP-P"),
                      ("HP-TIM", "TIM-P"),
                      ("HP-SRDI","SRDI-P"),
                      ("HP-CRDI","CRDI-P"),
                      ("HP-PRDI","PRDI-P"),
                      ("HP-PLM", "PLM-P"),
                      ("HP-UNEQ", "UNEQ-P"),
                      ("B3", "B3/CV-P"),
                      ("HP-REI", "REI-P"),
                      ]
            
        tableTitle = HP_HDR[nw]
        self.sdhIndivTable(fd, results, HP_LBL, tableTitle, nw, format)
        
        if (isLP):
            LP_HDR = ["LP", "VT"]
            if results['common']['enhancedRDI'] == 'DISABLE':
                if (isTU3):
                    LP_LBL = [
                        ("TU-AIS", "AIS-V"),
                        ("TU-LOP", "LOP-V"),
                        ("LP-TIM", "TIM-V"),
                        ("LP-RDI", "RDI-V"),
                        ("LP-PLM", "PLM-V"),
                        ("LP-UNEQ", "UNEQ-V"),
                        ("LP-BIP", "BIP2/CV-V"),
                        ("LP-REI", "REI-V"),
                        ]
                else:
                    LP_LBL = [
                        ("TU-AIS", "AIS-V"),
                        ("TU-LOP", "LOP-V"),
                        ("TU-LOM", "LOM-V"),
                        ("LP-RFI", "RFI-V"),
                        ("LP-TIM", "TIM-V"),
                        ("LP-RDI", "RDI-V"),
                        ("LP-PLM", "PLM-V"),
                        ("LP-EPLM", "EPLM-V"),
                        ("LP-UNEQ", "UNEQ-V"),
                        ("LP-BIP", "BIP2/CV-V"),
                        ("LP-REI", "REI-V"),
                        ]
            else:
                if (isTU3):
                    LP_LBL = [
                        ("TU-AIS", "AIS-V"),
                        ("TU-LOP", "LOP-V"),
                        ("LP-TIM", "TIM-V"),
                        ("LP-SRDI","SRDI-V"),
                        ("LP-CRDI","CRDI-V"),
                        ("LP-PRDI","PRDI-V"),
                        ("LP-PLM", "PLM-V"),
                        ("LP-UNEQ", "UNEQ-V"),
                        ("LP-BIP", "BIP2/CV-V"),
                        ("LP-REI", "REI-V"),
                        ]
                else:
                    LP_LBL = [
                        ("TU-AIS", "AIS-V"),
                        ("TU-LOP", "LOP-V"),
                        ("TU-LOM", "LOM-V"),
                        ("LP-RFI", "RFI-V"),
                        ("LP-TIM", "TIM-V"),
                        ("LP-SRDI","SRDI-V"),
                        ("LP-CRDI","CRDI-V"),
                        ("LP-PRDI","PRDI-V"),
                        ("LP-PLM", "PLM-V"),
                        ("LP-EPLM", "EPLM-V"),
                        ("LP-UNEQ", "UNEQ-V"),
                        ("LP-BIP", "BIP2/CV-V"),
                        ("LP-REI", "REI-V"),
                        ]
            tableTitle = LP_HDR[nw]
            self.sdhIndivTable(fd, results, LP_LBL, tableTitle, nw, format, isLP, isTU3)
        
    def sdhIndivTable(self, fd, results, labels, header, nw, format, isLP=False, isTU3=False):

        alarm_seconds = results['alarm_seconds']
        errors = results['errors']
        errors_rate = results['errors_rate']
        
        i = 0
        nvpq = []
        while (i < (labels.__len__() - 2) ):
            alarmsec = curtostr(alarm_seconds[self.getSTxAlmErrID(labels[i][0], 'alarm')])
            nvpq.append([labels[i][nw], alarmsec, ''])
            i += 1
        
        errorsec = curtostr(errors[self.getSTxAlmErrID(labels[i][0], 'error')])
        errorfloat = exp3tostr(errors_rate[self.getSTxAlmErrID(labels[i][0], 'error')])
        if nw == 0:
            if labels[i][nw] == 'B3':
                nvpq.append(["HP-B3", errorsec, errorfloat])
            elif isLP == True and labels[i][nw] == "LP-BIP":
                if isTU3 == True:
                    nvpq.append(["LP-B3", errorsec, errorfloat])
                else:
                    nvpq.append(["LP-BIP2", errorsec, errorfloat])
            else:
                nvpq.append([labels[i][nw], errorsec, errorfloat])
        else:
            nvpq.append([labels[i][nw], errorsec, errorfloat])

        i += 1
        errorsec = curtostr(errors[self.getSTxAlmErrID(labels[i][0], 'error')])
        errorfloat = exp3tostr(errors_rate[self.getSTxAlmErrID(labels[i][0], 'error')])
        nvpq.append([labels[i][nw], errorsec, errorfloat])
        
        table = []
        if format == 'pdf':
            colwidths = [2.35 * inch, 2.35 * inch, 2.35 * inch]
            style = \
                [   
                    ('BOX', (1, 0), (1, -1), 1, colors.grey),
                    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ]
            makeTable = self.createPdfTable
        else:
            colwidths = None
            style = []
            makeTable = self.createCsvTable
            
        makeTable(fd, header, nvpq, style, colwidths)
    
    def serviceDisruptionTable(self, fd, results, format):
        
        service_disr = results['bert']['service_disr']
        
        nvp = \
            [                
                ('Longest',  fmt_float3(service_disr[0])),
                ('Shortest', fmt_float3(service_disr[1])),
                ('Last ',    fmt_float3(service_disr[2])),
                ('Total',    fmt_float3(service_disr[3]))
            ]
        service_table = []
        style=[]
        if format == 'pdf':
            makeTable = self.createPdfTable
            colwidths = [3.525 * inch, 3.525 * inch]
            for n,v in nvp:
                service_table.append([n,v])
        elif format == 'csv':
            makeTable = self.createCsvTable
            colwidths = None
            names = []
            values = []
            for n,v in nvp:
                names.append(n)
                values.append(v)
            service_table.append(names)
            service_table.append(values)
        makeTable(fd, "Service Disruption (msec)", service_table,style,colwidths)
        
        
    def g821Table(self, fd, results, nw_standard, format):

        nw = nw_standard
        G821BEP = ["G.821", "Bit Error Performace"]
        BERTTitle = ["G.821", "BERT"]
        
        g821_table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            colwidths = [1.175 * inch, 1.175 * inch, 1.175 * inch, 1.175 * inch, 1.175 * inch, 1.175 * inch]
            g821_table.append([Paragraph('<font name = Helvetica size = 10><b>Pattern</b></font>', styleSheet['Normal']), '', '', Paragraph('<font name = Helvetica size = 10><b>'+ G821BEP[nw]+'</b></font>', styleSheet['Normal']), '', ''])
        else:
            makeTable = self.createCsvTable
            colwidths = None
            g821_table.append(["Pattern", "", "", G821BEP[nw], "", ""])

        bert = results['bert']
        setG821 = \
        (
            ['Current Bit', curtostr(bert['current_errors']), exp3tostr(bert['current_error_rate']), 'ES', curtostr(bert['es']), fmt_float(bert['es_p']) + '%'],
            ['Bit', curtostr(bert['errors'][0]), exp3tostr(bert['error_rate'][0]), 'SES', curtostr(bert['ses']), fmt_float(bert['ses_p']) + '%'],
            ['LOPS',curtostr(bert['alarm_seconds'][1]), '', 'EFS', curtostr(bert['efs']), fmt_float(bert['efs_p']) + '%'],
            ['', '', '', '', '', ''],
            ['', '', '', 'AS', curtostr(bert['as']), fmt_float(bert['as_p']) + '%'],
            ['', '', '', 'UAS', curtostr(bert['uas']), fmt_float(bert['uas_p']) + '%'],
        )
        g821_table.extend(setG821)
        style = \
            [   
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (3, 0), (3, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, 0), 1, colors.grey),
                ('BOX', (1, 0), (1, -1), 1, colors.grey),
                ('BOX', (2, 0), (2, -1), 1, colors.grey),
                ('BOX', (3, 1), (3, -1), 1, colors.grey),
                ('BOX', (4, 1), (4, -1), 1, colors.grey),
                ('BOX', (5, 1), (5, -1), 1, colors.grey),
                ('SPAN', (0, 0), (2, 0)),
            ]

        makeTable(fd, BERTTitle[nw], g821_table, style, colwidths)
        
    def g828Table(self, fd, results, nw_standard, isLP, isTU3, format):

        nw = nw_standard
        NEAREND = "Near End: "
        FAREND = "Far End: "
        NEHP_HDR = [NEAREND+"HP-B3", NEAREND+"CV-P"]
        FEHP_HDR = [FAREND+"HP-REI", FAREND+"REI-P"]
        NELP_HDR = [NEAREND+"LP-BIP2", NEAREND+"CV-V"]
        if (isTU3):
            NELP_HDR = [NEAREND+"LP-B3", NEAREND+"CV-V"]
        FELP_HDR = [FAREND+"LP-REI", FAREND+"REI-V"]
        
        Title = ["G.828", "GR-253 P/V"]

        g828_table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            colwidths = [1.175 * inch, 1.175 * inch, 1.175 * inch, 1.175 * inch, 1.175 * inch, 1.175 * inch]
            g828_table.append([Paragraph('<font name = Helvetica size = 10><b>%s</b></font>'%NEHP_HDR[nw], styleSheet['Normal']), '', '', Paragraph('<font name = Helvetica size = 10><b>%s</b></font>'%FEHP_HDR[nw], styleSheet['Normal']), '', ''])
        else:
            makeTable = self.createCsvTable
            colwidths = None
            g828_table.append([NEHP_HDR[nw], "", "", FEHP_HDR[nw], "", ""])
            
        ne = results['NG82X_meas'][2]
        fe = results['FG82X_meas'][2]

        if nw == 0:
            setG828HP = \
            (
                ['BE', curtostr(ne['be']), '', 'BE', curtostr(fe['be']), ''],
                ['BBE', curtostr(ne['bbe']),  exp3tostr(ne['bbe_r']), 'BBE', curtostr(fe['bbe']),  exp3tostr(fe['bbe_r'])],
                ['ES', curtostr(ne['es']),  fmt_float(ne['es_p']) + '%', 'ES', curtostr(fe['es']),  fmt_float(fe['es_p']) + '%'],
                ['SES', curtostr(ne['ses']),  fmt_float(ne['ses_p']) + '%', 'SES', curtostr(fe['ses']),  fmt_float(fe['ses_p']) + '%'],
                ['SEP', curtostr(ne['sep']),  exp3tostr(ne['sep_r']), 'SEP', curtostr(fe['sep']),  exp3tostr(fe['sep_r'])],
                ['AS', curtostr(ne['as']),  fmt_float(ne['as_p']) + '%', 'AS', curtostr(fe['as']),  fmt_float(fe['as_p']) + '%'],
                ['UAS', curtostr(ne['uas']),  fmt_float(ne['uas_p']) + '%', 'UAS', curtostr(fe['uas']),  fmt_float(fe['uas_p']) + '%'],
            )
        else:
            setG828HP = \
            (
                ['BE', curtostr(ne['be']), '', 'BE', curtostr(fe['be']), ''],
                ['ES', curtostr(ne['es']),  fmt_float(ne['es_p']) + '%', 'ES', curtostr(fe['es']),  fmt_float(fe['es_p']) + '%'],
                ['SES', curtostr(ne['ses']),  fmt_float(ne['ses_p']) + '%', 'SES', curtostr(fe['ses']),  fmt_float(fe['ses_p']) + '%'],
                ['AS', curtostr(ne['as']),  fmt_float(ne['as_p']) + '%', 'AS', curtostr(fe['as']),  fmt_float(fe['as_p']) + '%'],
                ['UAS', curtostr(ne['uas']),  fmt_float(ne['uas_p']) + '%', 'UAS', curtostr(fe['uas']),  fmt_float(fe['uas_p']) + '%'],
            )
        g828_table.extend(setG828HP)

        if (isLP):
            if format == 'pdf':
                g828_table.append([Paragraph('<font name = Helvetica size = 10><b>%s</b></font>'%NELP_HDR[nw], styleSheet['Normal']), '', '', Paragraph('<font name = Helvetica size = 10><b>%s</b></font>'%FELP_HDR[nw], styleSheet['Normal']), '', ''])
            else:
                g828_table.append([NELP_HDR[nw], "", "", FELP_HDR[nw], "", ""])
            
            ne = results['NG82X_meas'][3]
            fe = results['FG82X_meas'][3]

            if nw == 0:
                setG828LP = \
                (
                    ['BE', curtostr(ne['be']), '', 'BE', curtostr(fe['be']), ''],
                    ['BBE', curtostr(ne['bbe']),  exp3tostr(ne['bbe_r']), 'BBE', curtostr(fe['bbe']),  exp3tostr(fe['bbe_r'])],
                    ['ES', curtostr(ne['es']),  fmt_float(ne['es_p']) + '%', 'ES', curtostr(fe['es']),  fmt_float(fe['es_p']) + '%'],
                    ['SES', curtostr(ne['ses']),  fmt_float(ne['ses_p']) + '%', 'SES', curtostr(fe['ses']),  fmt_float(fe['ses_p']) + '%'],
                    ['SEP', curtostr(ne['sep']),  exp3tostr(ne['sep_r']), 'SEP', curtostr(fe['sep']),  exp3tostr(fe['sep_r'])],
                    ['AS', curtostr(ne['as']),  fmt_float(ne['as_p']) + '%', 'AS', curtostr(fe['as']),  fmt_float(fe['as_p']) + '%'],
                    ['UAS', curtostr(ne['uas']),  fmt_float(ne['uas_p']) + '%', 'UAS', curtostr(fe['uas']),  fmt_float(fe['uas_p']) + '%'],
                )
            else :
                setG828LP = \
                (
                    ['BE', curtostr(ne['be']), '', 'BE', curtostr(fe['be']), ''],
                    ['ES', curtostr(ne['es']),  fmt_float(ne['es_p']) + '%', 'ES', curtostr(fe['es']),  fmt_float(fe['es_p']) + '%'],
                    ['SES', curtostr(ne['ses']),  fmt_float(ne['ses_p']) + '%', 'SES', curtostr(fe['ses']),  fmt_float(fe['ses_p']) + '%'],
                    ['AS', curtostr(ne['as']),  fmt_float(ne['as_p']) + '%', 'AS', curtostr(fe['as']),  fmt_float(fe['as_p']) + '%'],
                    ['UAS', curtostr(ne['uas']),  fmt_float(ne['uas_p']) + '%', 'UAS', curtostr(fe['uas']),  fmt_float(fe['uas_p']) + '%'],
                )
            g828_table.extend(setG828LP)

        style = \
            [   
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (3, 0), (3, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, 0), 1, colors.grey),
                ('BOX', (1, 0), (1, -1), 1, colors.grey),
                ('BOX', (2, 0), (2, -1), 1, colors.grey),
                ('BOX', (3, 1), (3, -1), 1, colors.grey),
                ('BOX', (4, 1), (4, -1), 1, colors.grey),
                ('BOX', (5, 1), (5, -1), 1, colors.grey),
                ('SPAN', (0, 0), (2, 0)),
                ('SPAN', (3, 0), (5, 0)),
            ]
        if (isLP):
            if nw == 0:
                second_item_row = 8
            else:
                second_item_row = 6

            style = \
                [   
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                    ('ALIGN', (3, 0), (3, -1), 'LEFT'),
                    ('BOX', (0, 0), (-1, 0), 1, colors.grey),
                    ('BOX', (0, second_item_row), (-1, second_item_row), 1, colors.grey),
                    ('BOX', (1, 0), (1, -1), 1, colors.grey),
                    ('BOX', (2, 0), (2, -1), 1, colors.grey),
                    ('BOX', (3, 1), (3, -1), 1, colors.grey),
                    ('BOX', (4, 1), (4, -1), 1, colors.grey),
                    ('BOX', (5, 1), (5, -1), 1, colors.grey),
                    ('SPAN', (0, 0), (2, 0)),
                    ('SPAN', (3, 0), (5, 0)),
                    ('SPAN', (0, second_item_row), (2, second_item_row)),
                    ('SPAN', (3, second_item_row), (5, second_item_row)),
                ]
                    
        makeTable(fd, Title[nw], g828_table, style, colwidths)
        
    def g829Table(self, fd, results, nw_standard, format):
        
        nw = nw_standard
        NEAREND = "Near End: "
        FAREND = "Far End: "
        NERS_HDR = [NEAREND+"B1", NEAREND+"CV-S"]
        NEMS_HDR = [NEAREND+"B2", NEAREND+"CV-L"]
        FEMS_HDR = [FAREND+"MS-REI", FAREND+"REI-L"]
        Title = ["G.829", "GR-253 S/L"]
        g829_table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            colwidths = [1.175 * inch, 1.175 * inch, 1.175 * inch, 1.175 * inch, 1.175 * inch, 1.175 * inch]
            g829_table.append([Paragraph('<font name = Helvetica size = 10><b>%s</b></font>' % NERS_HDR[nw], styleSheet['Normal']), '', '', '', '', ''])
        else:
            makeTable = self.createCsvTable
            colwidths = None
            g829_table.append([NERS_HDR[nw], "", "", "", "", ""])

        ne = results['NG82X_meas'][0]
        
        g829_table.append(['BE', curtostr(ne['be']), '', '', '', ''])
        if nw == 0:
            g829_table.append(['BBE', curtostr(ne['bbe']), exp3tostr(ne['bbe_r']), '', '', ''])
        
        setG829 = \
        (
            ['ES', curtostr(ne['es']), fmt_float(ne['es_p']) + '%', '', '', ''],
            ['SES', curtostr(ne['ses']), fmt_float(ne['ses_p']) + '%', '', '', ''],
            ['AS', curtostr(ne['as']), fmt_float(ne['as_p']) + '%', '', '', ''],
            ['UAS', curtostr(ne['uas']), fmt_float(ne['uas_p']) + '%', '', '', ''],
        )
        g829_table.extend(setG829)

        if format == 'pdf':            
            g829_table.append([Paragraph('<font name = Helvetica size = 10><b>%s</b></font>' % NEMS_HDR[nw], styleSheet['Normal']), '', '', Paragraph('<font name = Helvetica size = 10><b>%s</b></font>' % FEMS_HDR[nw], styleSheet['Normal']), '', ''])
        else:
            g829_table.append([NEMS_HDR[nw], "", "", FEMS_HDR[nw], "", ""])

        ne = results['NG82X_meas'][1]
        fe = results['FG82X_meas'][1]
        g829_table.append(['BE', curtostr(ne['be']), '', 'BE', curtostr(fe['be']), ''])
        if nw == 0:
            g829_table.append(['BBE', curtostr(ne['bbe']), exp3tostr(ne['bbe_r']), 'BBE', curtostr(fe['bbe']), exp3tostr(fe['bbe_r'])])
        setB2 = \
        (
            ['ES', curtostr(ne['es']), fmt_float(ne['es_p']) + '%', 'ES', curtostr(fe['es']), fmt_float(fe['es_p']) + '%'],
            ['SES', curtostr(ne['ses']), fmt_float(ne['ses_p']) + '%', 'SES', curtostr(fe['ses']),  fmt_float(fe['ses_p']) + '%'],
            ['AS', curtostr(ne['as']), fmt_float(ne['as_p']) + '%', 'AS', curtostr(fe['as']), fmt_float(fe['as_p']) + '%'],
            ['UAS', curtostr(ne['uas']), fmt_float(ne['uas_p']) + '%', 'UAS', curtostr(fe['uas']), fmt_float(fe['uas_p']) + '%'],
        )
        g829_table.extend(setB2)

        if nw == 0:
            second_item_row = 7
        else:
            second_item_row = 6
        style = \
            [   
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (3, 0), (3, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, 0), 1, colors.grey),
                ('BOX', (0, second_item_row), (-1, second_item_row), 1, colors.grey),
                ('BOX', (1, 0), (1, -1), 1, colors.grey),
                ('BOX', (2, 0), (2, -1), 1, colors.grey),
                ('BOX', (3, 1), (3, -1), 1, colors.grey),
                ('BOX', (4, 1), (4, -1), 1, colors.grey),
                ('BOX', (5, 1), (5, -1), 1, colors.grey),
                ('SPAN', (0, 0), (5, 0)),
                ('SPAN', (0, second_item_row), (2, second_item_row)),
                ('SPAN', (3, second_item_row), (5, second_item_row)),
            ]

        makeTable(fd, Title[nw], g829_table, style, colwidths)
    def m2101Table(self, fd, results, nw_standard,isLP,isTU3, format):
        tables=['MS_Near','MS_Far','HP_Near','HP_Far','LP_Near','LP_Far']
        
        cmd = {
                   'MS_Near':1,
                   'MS_Far':1,
                   'HP_Near':2,
                   'HP_Far':2,
                   'LP_Near':3,
                   'LP_Far':3
              }
              
        tbTitle = {
                      "MS_Near":'M.2101 MS Near End -B2',
                      "MS_Far":'M.2101 MS Far End - MS-REI',
                      "HP_Near":'M.2101 HP Near End - HP-B3',
                      "HP_Far":'M.2101 HP Far End - HP-REI',
                      "LP_Near":'M.2101 LP Near End - LP-B3',
                      "LP_Far":'M.2101 LP Far End - LP-REI'
                  }
        NETU3_HDR = "M.2101 LP Near End - LP-B3"
        NELP_HDR = "M.2101 LP Near End - LP-BIP2"
        if not isLP:
            del tbTitle['LP_Near']
            del tbTitle['LP_Far']
            del cmd['LP_Near']
            del cmd['LP_Far']
            tables.remove('LP_Near')
            tables.remove('LP_Far')
        else:
            if isTU3:
                tbTitle["LP_Near"] = NETU3_HDR
            else:
                tbTitle["LP_Near"] = NELP_HDR

        M2101_criteria = results["M2101_criteria"]
        NM2101_meas     = results["NM2101_meas"]
        FM2101_meas     = results["FM2101_meas"]
        for i in tables:
            
            tableCriteria    = M2101_criteria[cmd[i]]
            if "Near" in i:
                tableMeas        = NM2101_meas[cmd[i]]
            else:
                tableMeas        = FM2101_meas[cmd[i]]
            
            tbName = tbTitle[i]
            start_time = tableMeas["start_time"]
            
            year  = start_time["year"]
            month = start_time["month"]
            day   = start_time["day"]
            hour  = start_time["hour"]
            min   = start_time["min"]
            sec   = start_time["sec"]
            
            FROM     = ""
            TO       = "" 
            Report   = ""
            hasIssue = False
            if((year+month+day+hour+min+sec)>0 and (year > 1970 and year<3000)):
                FROM = "%02d-%02d-%02d %02d:%02d:%02d"%(year,month,day,hour,min,sec)
            else:
                hasIssue = True
            
            stop_time = tableMeas["stop_time"]
            year      = stop_time["year"]
            month     = stop_time["month"]
            day       = stop_time["day"]
            hour      = stop_time["hour"]
            min       = stop_time["min"]
            sec       = stop_time["sec"]

            if((year+month+day+hour+min+sec)>0) and (year > 1970 and year<3000) and (not hasIssue):
                TO = "%02d-%02d-%02d %02d:%02d:%02d"%(year,month,day,hour,min,sec)
            
            Report = ""
            if tableMeas.has_key("is_pass")and (not hasIssue):
                key = tableMeas["is_pass"]
                reportMap = {0:'MAINT. ACCEPTABLE',
                             1:'MAINT. DEGRADED',
                             2:'MAINT. UNACCEPTABLE'
                            }
                if reportMap.has_key(key):
                    Report = reportMap.get(key)

            ES     = "%d"%tableMeas["errored_seconds"]
            perES  = fmt_float(tableMeas["fes"])+'%'
            SES    = "%d"%tableMeas["severely_errored_seconds"]
            perSES = fmt_float(tableMeas["fses"])+'%'

            ESPRO  = "%d"%tableCriteria["es_rpo"]
            SESPRO = "%d"%tableCriteria["ses_rpo"]
            ESDPL  = "%d"%tableCriteria["es_dpl"]
            SESDPL = "%d"%tableCriteria["ses_dpl"]
            ESUPL  = "%d"%tableCriteria["es_upl"]
            SESUPL = "%d"%tableCriteria["ses_upl"]

            nvpPDF=\
                [["From",FROM,"",""],
                 ["To",TO,"",""],
                 ["Report",Report,"",""],
                 ["ES",ES,"SES",SES],
                 ["%ES",perES,"%SES",perSES],
                 ["ES RPO",ESPRO,"SES RPO",SESPRO],
                 ["ES DPL",ESDPL,"SES DPL",SESDPL],
                 ["ES UPL",ESUPL,"SES UPL",SESUPL]
                 ]
            nvpCSV=\
                [["From",FROM],
                 ["To",TO],
                 ["Report",Report],
                 ["ES",ES],
                 ["SES",SES],
                 ["%ES",perES],
                 ["%SES",perSES],
                 ["ES RPO",ESPRO],
                 ["SES RPO",SESPRO],
                 ["ES DPL",ESDPL],
                 ["SES DPL",SESDPL],
                 ["ES UPL",ESUPL],
                 ["SES UPL",SESUPL]]

            M2101_result_table = []
            if format == 'pdf':
                colwidths = [1.7625 * inch, 1.7625 * inch, 1.7625 * inch, 1.7625 * inch]
                makeTable = self.createPdfTable
                for n in nvpPDF:
                    M2101_result_table.append(n)
            elif format == 'csv':
                colwidths = None
                makeTable = self.createCsvTable
                values    = []
                names     = []
                for n,v in nvpCSV:
                    names.append(n)
                    values.append(v)
                M2101_result_table.append(names)
                M2101_result_table.append(values)
            else:
                print("Format Not Specified, Exiting23")
                return

            style= \
                [
                    ('GRID',(0,0),(-1,-1),0.5,colors.grey),
                    ('BOX',(0,0),(-1,-1),1,colors.grey),
                    ('SPAN',(1,0),(3,0)),
                    ('SPAN',(1,1),(3,1)),
                    ('SPAN',(1,2),(3,2)),
                    ('BACKGROUND', (0,0), (-1, -1), colors.lavender),
                ]
            makeTable(fd, tbName, M2101_result_table, style,colwidths)
        pass
    def m2110Table(self, fd, results, nw_standard,isLP,isTU3,bert_type, format):
        
        tables=['MS_Near','MS_Far','HP_Near','HP_Far','LP_Near','LP_Far','BIT']
        
        cmd = {
                   'MS_Near':1,
                   'MS_Far':1,
                   'HP_Near':2,
                   'HP_Far':2,
                   'LP_Near':3,
                   'LP_Far':3,
                   'BIT':-1
              }
              
        tbTitle = {
                      "MS_Near":'M.2110 MS Near End - B2',
                      "MS_Far":'M.2110 MS Far End - MS-REI',
                      "HP_Near":'M.2110 HP Near End - HP-B3',
                      "HP_Far":'M.2110 HP Far End - HP-REI',
                      "LP_Near":'M.2110 LP Near End - LP-BIP',
                      "LP_Far":'M.2110 LP Far End - LP-REI',
                      'BIT':'M.2110 BIT'
                  }
        NETU3_HDR = "M.2110 LP Near End - LP-B3"
        NELP_HDR = "M.2110 LP Near End - LP-BIP2"
        if not isLP:
            del tbTitle['LP_Near']
            del tbTitle['LP_Far']
            del cmd['LP_Near']
            del cmd['LP_Far']
            tables.remove('LP_Near')
            tables.remove('LP_Far')
        else:
            if isTU3:
                tbTitle["LP_Near"] = NETU3_HDR
            else:
                tbTitle["LP_Near"] = NELP_HDR
                
        if bert_type != 'BERT':
            del tbTitle['BIT']
            del cmd['BIT']
            tables.remove('BIT')
        
        M2110_criteria  = results["M2110_criteria"]
        NM2110_meas     = results["NM2110_meas"]
        FM2110_meas     = results["FM2110_meas"]
        for i in tables:
            tableMeas     = None
            tableCriteria = None
            if i == "BIT":
                tableCriteria    = results["M2110_criteria_BIT"][0]
                tableMeas        = results["BIT2110_meas"]
            else:
                tableCriteria    = M2110_criteria[cmd[i]]
                if "Near" in i:
                    tableMeas        = NM2110_meas[cmd[i]]
                else:
                    tableMeas        = FM2110_meas[cmd[i]]

            tbName     = tbTitle[i]
            start_time = tableMeas["start_time"]

            year  = start_time["year"]
            month = start_time["month"]
            day   = start_time["day"]
            hour  = start_time["hour"]
            min   = start_time["min"]
            sec   = start_time["sec"]
            
            FROM     = ""
            TO       = "" 
            Report   = ""
            hasIssue = False
            if((year+month+day+hour+min+sec)>0 and (year > 1970 and year<3000)):
                FROM = "%02d-%02d-%02d %02d:%02d:%02d"%(year,month,day,hour,min,sec)
            else:
                hasIssue = True
            
            stop_time = tableMeas["stop_time"]
            year      = stop_time["year"]
            month     = stop_time["month"]
            day       = stop_time["day"]
            hour      = stop_time["hour"]
            min       = stop_time["min"]
            sec       = stop_time["sec"]
            
            if((year+month+day+hour+min+sec)>0 and (year > 1970 and year<3000)) and (not hasIssue):
                TO = "%02d-%02d-%02d %02d:%02d:%02d"%(year,month,day,hour,min,sec)
            
            if tableMeas.has_key("is_pass")  and (not hasIssue):
                key = tableMeas["is_pass"]
                reportMap = {0:'BIS. ACCEPTED',
                             1:'BIS. PROVISIONAL',
                             2:'BIS. ABORTED'
                             }
                if reportMap.has_key(key):
                    Report = reportMap.get(key)

            ES     = "%d"%tableMeas["errored_seconds"]
            perES  = fmt_float(tableMeas["fes"])+'%'
            SES    = "%d"%tableMeas["severely_errored_seconds"]
            perSES = fmt_float(tableMeas["fses"])+'%'

            ESBISO  = "%d"%tableCriteria["es_biso"]
            SESBISO = "%d"%tableCriteria["ses_biso"]
            ESS1    = "%d"%tableCriteria["es_s1"]
            SESS1   = "%d"%tableCriteria["ses_s1"]
            ESS2    = "%d"%tableCriteria["es_s2"]
            SESS2   = "%d"%tableCriteria["ses_s2"]

            nvpPDF=\
                [["From",FROM,"",""],
                 ["To",TO,"",""],
                 ["Report",Report,"",""],
                 ["ES",ES,"SES",SES],
                 ["%ES",perES,"%SES",perSES],
                 ["ES BISO",ESBISO,"SES BISO",SESBISO],
                 ["ES S1",ESS1,"SES S1",SESS1],
                 ["ES S2",ESS2,"SES S2",SESS2]
                 ]
            nvpCSV=\
                [["From",FROM],
                 ["To",TO],
                 ["Report",Report],
                 ["ES",ES],
                 ["SES",SES],
                 ["%ES",perES],
                 ["%SES",perSES],
                 ["ES BISO",ESBISO],
                 ["SES BISO",SESBISO],
                 ["ES S1",ESS1],
                 ["SES S1",SESS1],
                 ["ES S2",ESS2],
                 ["SES S2",SESS2]]

            M2110_result_table = []
            if format == 'pdf':
                colwidths = [1.7625 * inch, 1.7625 * inch, 1.7625 * inch, 1.7625 * inch]
                makeTable = self.createPdfTable
                for n in nvpPDF:
                    M2110_result_table.append(n)
            elif format == 'csv':
                colwidths = None
                makeTable = self.createCsvTable
                values    = []
                names     = []
                for n,v in nvpCSV:
                    names.append(n)
                    values.append(v)
                M2110_result_table.append(names)
                M2110_result_table.append(values)
            else:
                print("Format Not Specified, Exiting23")
                return

            style= \
                [
                    ('GRID',(0,0),(-1,-1),0.5,colors.grey),
                    ('BOX',(0,0),(-1,-1),1,colors.grey),
                    ('SPAN',(1,0),(3,0)),
                    ('SPAN',(1,1),(3,1)),
                    ('SPAN',(1,2),(3,2)),
                    ('BACKGROUND', (0,0), (-1, -1), colors.lavender),
                ]
            makeTable(fd, tbName, M2110_result_table, style,colwidths)
        pass
    def SDHRxTxPathMapping(self, config, trx):
        mapping = ""
        linenum = 1;
        
        stx = config[trx]
        Mapping = stx['mapping']
        tuvt = Mapping['tuvt']
        austs = Mapping['austs']
        payload = Mapping['payload']
        if payload == 'VC4_64C':
            mapping = "AU4-64C-VC4-64C"
        elif payload == 'VC4_16C':
            mapping = "AU4-16C[%d]-VC4-16C"%(stx['channel']+1)
        elif payload == 'VC4_4C':
            mapping = "AU4-4C[%d]-VC4-4C"%(stx['channel']+1)
        elif payload == 'VC4B':
            mapping = "AUG[%d]-AU-4-VC4"%(stx['channel']+1)
        elif payload == 'VC3B':
            if austs == "AU4":
                mapping = "AUG[%d]-AU-4-TUG3[%d]-TU-3-VC-3"%(stx['channel']+1,stx['tugau']+1)
            else:
                mapping = "AUG[%d]-AU-3[%d]-VC-3"%(stx['channel']+1,stx['tugau']+1)
        elif payload == 'VC12B':
            if austs == "AU4":
                mapping = "AUG[%d]-AU-4-TUG3[%d]-TUG-2[%d]\n-TU-12[%d]-VC-12"%(stx['channel']+1,stx['tugau']+1,stx['tug2']+1,stx['tu']+1)
                linenum = 2
            else:
                mapping = "AUG[%d]-AU-3[%d]-TUG-2[%d]-TU-12[%d]-VC-12"%(stx['channel']+1,stx['tugau']+1, stx['tug2']+1,stx['tu']+1)
        elif payload == 'VC11B':
            tutype = 'TU-11'
            if tuvt == 'TU12':
                tutype = 'TU-12'
            if austs == "AU4":
                mapping = "AUG[%d]-AU-4-TUG3[%d]-TUG-2[%d]\n-%s[%d]-VC-11"%(stx['channel']+1,stx['tugau']+1, stx['tug2']+1, tutype, stx['tu']+1)
                linenum = 2
            else:
                mapping = "AUG[%d]-AU-3[%d]-TUG-2[%d]-%s[%d]-VC-11"%(stx['channel']+1,stx['tugau']+1, stx['tug2']+1, tutype, stx['tu']+1)

        self.write_log("SDHRxTxPathMapping(%s):payload=%s, austs=%s, tuvt=%s, mapping=%s"%(trx, payload, austs, tuvt, mapping))
        return mapping, linenum

    def SonetRxTxPathMapping(self, config, trx):
        mapping = ""
        linenum = 1;

        stx = config[trx]
        Mapping = stx['mapping']
        payload = Mapping['payload']
        if payload == 'STS192C':
            mapping = "STS-192C-STS-192c SPE"
        elif payload == 'STS48C':
            mapping = "STS-48c[%d]-STS-48c SPE"%(stx['channel']+1)
        elif payload == 'STS12C':
            mapping = "STS-12c[%d]-STS-12c SPE"%(stx['channel']+1)
        elif payload == 'STS3C':
            mapping = "STS-3c[%d]-STS-3c SPE"%(stx['channel']+1)
        elif payload == 'STS1P':
            mapping = "STS-1[%d]-STS-1 SPE"%(stx['channel']+1)
        elif payload == 'VT2B':
            mapping = "STS-1[%d]-VT GRP[%d]-VT2[%d]-VT2 SPE"%(stx['channel']+1,stx['tug2']+1,stx['tu']+1)
        elif payload == 'VT1B':
            mapping = "STS-1[%d]-VT GRP[%d]-VT1.5[%d]-VT1.5 SPE"%(stx['channel']+1,stx['tug2']+1,stx['tu']+1)
        print "SonetRxTxPathMapping(%s):payload=%s, mapping=%s"%(trx, payload, mapping)
        return mapping, linenum

    def getPRBSLabel(self, prbstype):
        PRBS_pattern = {'2E31':'2^31-1', 
                        '2E23' :'2^23-1',
                        '2E20' :'2^20-1',
                        '2E15' :'2^15-1',
                        '2E11' :'2^11-1',
                        '2E9'  :'2^9-1',
                        '2E7'  :'2^7-1',
                        '2E6'  :'2^6-1',
                        'ALL0' :'0000',
                        'ALL1' :'1111',
                        'ALT10':'1010',
                        'USER' :'USER',
                        '20ITU':'20ITU',
                        'QRS'  :'QRSS',
                        '1IN4' :'1-4',
                        '1IN8' :'1-8',
                        '1IN16':'1-16',
                        '3IN24':'3-24',
                        'FOX'  :'FOX',
                        '55DLY':'DALY55',
                        'IDLE' :'IDLE',
                        '55OCT':'OCT55', 
                        'YEL'  :'YEL',
                        'NONE' :'NONE'
                        }
        return PRBS_pattern[prbstype]

    def sdhRxTxSettingSetup(self, fd, config, format):
        
        try:
            setup = config['config']
        except:
            self.log_error('Interface setup data not found!')
            return
            
        tx_standard = setup['tx_standard']
        rx_standard = setup['rx_standard']
        tx_lineRate = setup['tx_line_rate']
        rx_lineRate = setup['rx_line_rate']
        tx_application = setup['tx_application']
        rx_application = setup['rx_application']

        nw = 0
        if (rx_standard == "SONET"):
            nw = 1
            stm = setup['sonet']
        else:
            stm = setup['stm']
        
        txlinerate = self.getLineRateLabel(setup['tx_line_rate'], nw)
        rxlinerate = self.getLineRateLabel(setup['rx_line_rate'], nw)

        testModeCode = setup['mode'];
        
        tx_chnum = ""
        rx_chnum = ""
        tx_linenum = 1
        rx_linenum = 1
        if (tx_standard == "SONET"):
            tx_chnum, tx_linenum = self.SonetRxTxPathMapping(stm, 'tx')
        else:
            tx_chnum, tx_linenum = self.SDHRxTxPathMapping(stm, 'tx')
        if (rx_standard == "SONET"):
            rx_chnum, rx_linenum = self.SonetRxTxPathMapping(stm, 'rx')
        else:
            rx_chnum, rx_linenum = self.SDHRxTxPathMapping(stm, 'rx')
            
        tx_linetype = stm['tx']['linetype']
        rx_linetype = stm['rx']['linetype']
        
        if testModeCode == 'LINETHRU' or testModeCode == 'PAYLOADTHRU':
            tx_clocksource = self.getClockLabel('LOOP')
        else:
            tx_clocksource = self.getClockLabel(stm['tx']['txclk'])

        tx_framing = stm['tx']['framing']
        rx_framing = stm['rx']['framing']
        
        txMapping = stm['tx']['mapping']
        tx_tuvt = txMapping['tuvt']
        tx_austs = txMapping['austs']
        tx_autype = tx_austs  if (tx_tuvt == "NONE") else (" "+tx_tuvt)
        tx_payload = txMapping['payload'] +' '+ tx_application 
        otherch = stm['tx']['unass']
        if (otherch == 'UNEQ'):
            otherch = 'Unequipped'
        else:
            otherch = 'Broadcast'
            
        rxMapping = stm['rx']['mapping']
        rx_tuvt = rxMapping['tuvt']
        rx_austs = rxMapping['austs']
        rx_autype = rx_austs  if (rx_tuvt == "NONE") else (" "+rx_tuvt)
        rx_payload = rxMapping['payload'] +' '+ rx_application 
        
        txPattern = stm['bert']['tx_pattern']
        tx_patternType = txPattern['type']
        tx_patTypelabel = self.getPRBSLabel(tx_patternType)
        tx_patternMode = txPattern['mode']
        tx_patternInversion = "";
        txuserpat = ""
        if tx_patternType in ('2E31', '2E23', '2E20', '2E15', '2E11', '2E9', '2E7', '2E6'):
            tx_patternInversion = txPattern['inv']
        elif tx_patternType == 'USER':
            txuserpatid = txPattern['user_pattern_id']-1
            txuserpat = binary(txPattern['userPattern'][txuserpatid], 16)

        rxPattern = stm['bert']['rx_pattern']
        rx_patternType = rxPattern['type']
        rx_patternMode = rxPattern['mode']

        rx_patTypelabel = ""
        rx_patternInversion = "";
        rxuserpat = ""
        if rx_patternMode == 'BERT': 
            rx_patTypelabel = self.getPRBSLabel(rx_patternType)
            if rx_patternType in ('2E31', '2E23', '2E20', '2E15', '2E11', '2E9', '2E7', '2E6'):
                rx_patternInversion = rxPattern['inv']
            elif rx_patternType == 'USER':
                rxuserpatid = rxPattern['user_pattern_id']-1
                rxuserpat = binary(rxPattern['userPattern'][rxuserpatid], 16)

        txrxsettings_table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            #colwidths = [1.7625 * inch, 1.7625 * inch, 1.7625 * inch, 1.7625 * inch]
            #colwidths = [2.35 * inch, 2.35 * inch, 2.35 * inch]
            colwidths = [1.4 * inch, 2.8 * inch, 2.8 * inch]
            txrxsettings_table.append(['', Paragraph('<font name = Helvetica size = 10><b>TX</b></font>', styleSheet['Normal']), Paragraph('<font name = Helvetica size = 10><b>RX</b></font>', styleSheet['Normal'])])
        else:
            makeTable = self.createCsvTable
            colwidths = None
            txrxsettings_table.append(["", "TX", "RX"])
      
        setConfig = \
        (
            ['Standard', tx_standard, rx_standard],
            ['Rate',   txlinerate, rxlinerate], 
            ['Line Type', tx_linetype, rx_linetype],
            #['Wave Length', '', ''],
            ['Framing', rx_framing,  tx_framing],
            ['Clock', tx_clocksource, '']
        )
        txrxsettings_table.extend(setConfig)

        if tx_clocksource == 'Internal':
            tx_offset = fmt_float_pre(stm['tx']['offset'], 1)
            txrxsettings_table.append(['Clock offset', tx_offset + ' ppm', ''])
        
        txrxsettings_table.append(['Path', tx_chnum, rx_chnum])
        if (txMapping['payload'] != 'VC4_64C' and txMapping['payload'] != 'STS192C'):
            txrxsettings_table.append(['Other Channels',otherch, ""])
        if testModeCode == 'SINGLE':
            txrxsettings_table.append(['Pattern Type', tx_patTypelabel, rx_patTypelabel])
            if tx_patternType in ('2E31', '2E23', '2E20', '2E15', '2E11', '2E9', '2E7', '2E6'):
                txrxsettings_table.append(['Pattern Inversion', tx_patternInversion, rx_patternInversion])
                self.write_log("txrxsettings_table.append:txinv=%s, rxinv=%s"%(tx_patternInversion, rx_patternInversion))
            elif tx_patternType == 'USER':
                txrxsettings_table.append(['User Pattern', txuserpat, rxuserpat])
                self.write_log("txrxsettings_table.append:usrpat=%d,%s, usrpat=%d,%s"%(txuserpatid, txuserpat, rxuserpatid, rxuserpat))
        else: # Thru mode, don't display Tx side. 
            if rx_patternMode == 'BERT':
                txrxsettings_table.append(['Pattern Type', "", rx_patTypelabel])
                if tx_patternType in ('2E31', '2E23', '2E20', '2E15', '2E11', '2E9', '2E7', '2E6'):
                    txrxsettings_table.append(['Pattern Inversion', "", rx_patternInversion])
                    self.write_log("txrxsettings_table.append:txinv=%s, rxinv=%s"%("", rx_patternInversion))
                elif tx_patternType == 'USER':
                    txrxsettings_table.append(['User Pattern', "", rxuserpat])
                    self.write_log("txrxsettings_table.append:usrpat=%d,%s, usrpat=%d,%s"%(txuserpatid, txuserpat, rxuserpatid, rxuserpat))
                
        style = \
            [   
                ('ALIGN', (1, 0), (2, 0), 'CENTER'),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, 0), 1, colors.grey),
                ('BOX', (1, 0), (1, -1), 1, colors.grey)
            ]
            
        #print "TXrxsetting tabel =", txrxsettings_table
        makeTable(fd, 'Tx/Rx Settings', txrxsettings_table, style, colwidths)    

    def captureSetupFC(self, fd, config, format):
        try:
            setup = config['config']['ether']['pcapConfig']['FCPcapConf']
        except:
            self.write_log('Capture setup data not found!', 'Error')
            return

        capture_table = []
        capture_table.append(['      ','Number', 'DID', 'SID'])
            
        max_filters = len(setup)
        index = 0
        while index < max_filters:
            filter_enable = setup[index]['enable']
            if filter_enable == 'ENABLE':
                filter_enable = 'Enable'
            else:
                filter_enable = 'Disable'
            if setup[index]['did_filter'] == 'ENABLE':
                DID = '0x%.2X%.2X%.2X'%(setup[index]['D_ID'][0], setup[index]['D_ID'][1], setup[index]['D_ID'][2])
            else:
                DID = 'Disable'

            if setup[index]['sid_filter'] == 'ENABLE':
                SID = '0x%.2X%.2X%.2X'%(setup[index]['S_ID'][0], setup[index]['S_ID'][1], setup[index]['S_ID'][2])
            else:
                SID = 'Disable'
            row = [filter_enable, str(index+1), DID, SID]
            capture_table.append(row)
            index = index + 1

        if format == 'pdf':
            makeTable = self.createPdfTable
        elif format == 'csv':
            makeTable = self.createCsvTable 
            
        makeTable(fd, 'Capture Setup', capture_table)
        
    def portSetupFC(self, fd, config, format):
        try:
            setup = config['config']['ether']['portConfig']
        except:
            self.write_log('Ports setup data not found!', 'Error')
            return

        portID = get_param(setup, 'portID')
        self.testport = get_param(setup, 'port_interface')
        testinterface = get_param(setup, 'fciface')

        if self.testport != 'SFP':
            self.write_log("Test Port is not SFP in portSetupFC")

        ports_config = \
            [
                ('Port ID', portID),
                ('Test Port',self.testport),
                ('Test Interface',testinterface),                    
            ]              

        port_table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
             
            for n,v in ports_config:
                port_table.append([n,v])
                
        elif format == 'csv':
            makeTable = self.createCsvTable 
            for n,v in ports_config:
                port_table.append([n,v])
            
        makeTable(fd, 'Port Setup', port_table)

    def captureSetup(self, fd, config, format):
        try:
            setup = config['config']['ether']['pcapConfig']['filter']
        except:
            self.write_log('Capture setup data not found!', 'Error')
            return

        capture_table = []
        capture_table.append(['      ','Number',\
                            'MAC Source', 'MAC Destination', 'MAC', 'Ether Type', 'VLAN ID',\
                            'IP Source', 'IP Destination', 'IP',\
                            'Error','Checksum', 'Test Frame', 'Packet Length'])
            
        max_filters = len(setup)
        index = 0
        while index < max_filters:
            cur_filter = setup[index]
            filter_enable = cur_filter['enable']
            if filter_enable == 1:
                filter_enable = 'Enable'
            else:
                filter_enable = 'Disable'

            number = str(index+1)

            #MAC layer
            if cur_filter['type']['src_mac'] == 1:
                mac_source = '%.2X-%.2X-%.2X-%.2X-%.2X-%.2X'%(cur_filter['type']['src_macaddr'][0], cur_filter['type']['src_macaddr'][1],cur_filter['type']['src_macaddr'][2],\
                                        cur_filter['type']['src_macaddr'][3], cur_filter['type']['src_macaddr'][4],cur_filter['type']['src_macaddr'][5])
            else:
                mac_source = 'Disable'

            if cur_filter['type']['dst_mac'] == 1:
                mac_destination = '%.2X-%.2X-%.2X-%.2X-%.2X-%.2X'%(cur_filter['type']['dst_macaddr'][0], cur_filter['type']['dst_macaddr'][1],cur_filter['type']['dst_macaddr'][2],\
                                        cur_filter['type']['dst_macaddr'][3], cur_filter['type']['dst_macaddr'][4],cur_filter['type']['dst_macaddr'][5])
            else:
                mac_destination = 'Disable'
 
            MAC = self.MACIPTypeCheck(cur_filter['type'], 'ucast_mac', 'mcast_mac', 'bcast_mac')

            if cur_filter['type']['ether_type'] == 1:
                ether_type = int_to_hex(cur_filter['type']['ether_type_num'], 4, True)
            else:
                ether_type = 'Disable'

            VLAN_ID = ""
            if cur_filter['type']['vlan1'] == 1:
                VLAN_ID += 'ID 1:'+str(cur_filter['type']['vlan1_id'])
            else:
                VLAN_ID += 'ID 1:Disable'
            if cur_filter['type']['vlan2'] == 1:
                VLAN_ID += ',ID 2:'+str(cur_filter['type']['vlan2_id'])
            else:
                VLAN_ID += ',ID 2:Disable'
            if cur_filter['type']['vlan3'] == 1:
                VLAN_ID += ',ID 3:'+str(cur_filter['type']['vlan3_id'])
            else:
                VLAN_ID += ',ID 3:Disable'
            if VLAN_ID.startswith(","):
                VLAN_ID = VLAN_ID[1:]
            if len(VLAN_ID) == 0:
                VLAN_ID = 'N/A'

            #IP layer
            if cur_filter['type']['src_ip'] == 1:
                ip_source = '%d.%d.%d.%d'%(cur_filter['type']['src_ipaddr'][0], cur_filter['type']['src_ipaddr'][1],\
                                        cur_filter['type']['src_ipaddr'][2], cur_filter['type']['src_ipaddr'][3])
            else:
                ip_source = 'Disable'

            if cur_filter['type']['dst_ip'] == 1:
                ip_destination = '%d.%d.%d.%d'%(cur_filter['type']['dst_ipaddr'][0], cur_filter['type']['dst_ipaddr'][1],\
                                        cur_filter['type']['dst_ipaddr'][2], cur_filter['type']['dst_ipaddr'][3])
            else:
                ip_destination = 'Disable'

            IP = self.MACIPTypeCheck(cur_filter['type'], 'ucast_ip', 'mcast_ip', 'bcast_ip')

            #other
            error = ''
            if cur_filter['error']['bit_error'] == 1:
                error += 'Bit Error'
            if cur_filter['error']['fcs_error'] == 1:
                error += ',FCS Error'
            if error.startswith(","):
                error = error[1:]
            if len(error) == 0:
                error = 'N/A'
                
            checksum = ''
            if cur_filter['error']['l3_chksum'] == 1:
                checksum += 'IP'
            if cur_filter['error']['l4_chksum'] == 1:
                checksum += ',TCP'
            if checksum.startswith(","):
                checksum = checksum[1:]
            if len(checksum) == 0:
                checksum = 'N/A'

            test_frame = ''
            if cur_filter['test_frame'] == 1:
                test_frame += 'Test Frame'
            if cur_filter['non_test_frame'] == 1:
                test_frame += ',Non Test Frame'
            if cur_filter['type']['tcp'] == 1:
                test_frame += ',TCP Frame'
            if cur_filter['type']['udp'] == 1:
                test_frame += ',UDP Frame'
            if test_frame.startswith(","):
                test_frame = test_frame[1:]
            if len(test_frame) == 0:
                test_frame = 'N/A'

            packet_length = ''
            if cur_filter['length']['jumbo'] == 1:
                packet_length += 'Over 1518'
            if cur_filter['length']['_1024'] == 1:
                packet_length += ',1518'
            if cur_filter['length']['_512'] == 1:
                packet_length += ',1023'
            if cur_filter['length']['_256'] == 1:
                packet_length += ',511'
            if cur_filter['length']['_128'] == 1:
                packet_length += ',255'
            if cur_filter['length']['_65'] == 1:
                packet_length += ',217'
            if cur_filter['length']['_64'] == 1:
                packet_length += ',64'
            if cur_filter['length']['runt'] == 1:
                packet_length += ',<64'
            if packet_length.startswith(","):
                packet_length = packet_length[1:]
            if len(packet_length) == 0:
                packet_length = 'N/A'

            #generate row data
            row = [filter_enable, number,\
                mac_source, mac_destination, MAC, ether_type, VLAN_ID,\
                ip_source, ip_destination, IP,
                error, checksum,test_frame,packet_length]
            capture_table.append(row)
            index = index + 1

        if format == 'pdf':
            makeTable = self.createPdfTable
            
            #split capture table here,because it's too long
            maxcolumnwidth = 4
            curcolumnwidth = len(capture_table[0])
            table_count = curcolumnwidth/maxcolumnwidth
            if curcolumnwidth%maxcolumnwidth != 0:
                table_count += 1
            for i in range(0, table_count):
                capture_table_i = []
                for row in capture_table:
                    start = (i*maxcolumnwidth)
                    end = start+maxcolumnwidth
                    if end > curcolumnwidth:
                        end = curcolumnwidth
                    capture_table_i.append(row[start:end])
                makeTable(fd, 'Capture Filter Setup Part-'+str(i+1), capture_table_i)
        elif format == 'csv':
            makeTable = self.createCsvTable 
            makeTable(fd, 'Capture Filter Setup', capture_table)
        
    def MACIPTypeCheck(self, root, ucastkey, mcastkey, bcastkey):
        value = ""
        if root[ucastkey] == 1:
            value += "Unicast"
        if root[mcastkey] == 1:
            value += ",Multicast"
        if root[bcastkey] == 1:
            value += ",Broadcast"
        if value.startswith(","):
            value = value[1:]
        if len(value) == 0:
            value = 'N/A'
        return value
        

    def portSetup(self, fd, config, format):
        try:
            setup = config['config']['ether']['portConfig']
        except:
            self.write_log('Ports setup data not found!', 'Error', sys.exc_info())
            return
            
        self.portID = get_param(setup, 'portID')        
        self.interface = get_param(setup, 'port_interface')      
        self.an = get_param(setup, 'an', NYNA)
        
        portID = 'P%d' % int(self.portID)
        interface = self.interface
        an = self.an
        
        if interface == 'RJ45':
            #pause_enabled = get_param(setup, 'pause_enabled', ENDI)
            #pause_delay = get_param(setup, 'pause')
            pause_enabled = get_param(setup, 'pause', ENDI)
            pause_delay = get_param(setup, 'fepfd')
            asymp = get_param(setup, 'asymp', ENDI)
            linerate = get_param(setup, 'port_rate')
            duplex = get_param(setup, 'port_duplex')
            pol = get_param(setup, 'pol')
            _1Gfull = get_param(setup, '_1Gfull', NYNA)
            _1Ghalf = get_param(setup, '_1Ghalf', NYNA)
            _100Mfull = get_param(setup, '_100Mfull', NYNA)
            _100Mhalf = get_param(setup, '_100Mhalf', NYNA)
            _10Mfull = get_param(setup, '_10Mfull', NYNA)
            _10Mhalf = get_param(setup, '_10Mhalf', NYNA)
            interface_type = 'LAN'
            if an == 'No':
                nvp = \
                [
                    ('Port ID', portID),
                    ('Test Interface', interface),
                    ('Interface Type', linerate),
                    ('Pause Enabled', pause_enabled),
                    (Paragraph('<para><font>Pause Frame Delay (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), pause_delay),                    
                    ('Polarity', pol),
                    ('Auto-Negotiation', an),
                ]              
            else:
                nvp = \
                [
                    ('Port ID', portID),
                    ('Test Interface', interface),
                    ('Pause Enabled', pause_enabled),
                    (Paragraph('<para><font>Pause Frame Delay (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), pause_delay),                    
                    ('Polarity', pol),
                    ('Auto-Negotiation', an),
                    ('Asymmetric Pause', asymp),
                    ('1000M Full Duplex Advertisment', _1Gfull),
                    ('1000M Half Duplex Advertisment', _1Ghalf),
                    ('100M Full Duplex Advertisment', _100Mfull),
                    ('100M Half Duplex Advertisment', _100Mhalf),
                    ('10M Full Duplex Advertisment', _10Mfull),
                    ('10M Half Duplex Advertisment', _10Mhalf)
                ]
             
        elif interface == 'SFP':
            #pause_enabled = get_param(setup, 'pause_enabled', ENDI)
            #pause_delay = get_param(setup, 'pause')
            pause_enabled = get_param(setup, 'pause', ENDI)
            pause_delay = get_param(setup, 'gepfd')
            asymp = get_param(setup, 'asymp', ENDI)
            linerate = get_param(setup, 'sfpiface')
            duplex = pol = _1Gfull = _1Ghalf = _100Mfull = _100Mhalf = _10Mfull = _10Mhalf = NA
            interface_type = get_param(setup, 'sfpiface')
            
            nvp = \
            [
                ('Port ID', portID),
                ('Test Interface', interface),
                ('Interface Type', interface_type),                    
                ('Pause Enabled', pause_enabled),
                (Paragraph('<para><font>Pause Frame Delay (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), pause_delay),                    
                ('Auto-Negotiation', an),
            ]              
            if an != 'No':
                add = [('Asymmetric Pause', asymp)]
                nvp.extend(add)
            
        elif interface == 'XFP':
            linerate = get_param(setup, 'port_rate')
            duplex = get_param(setup, 'port_duplex')
            #pause_enabled = get_param(setup, 'pause_enabled', ENDI)
            #pause_delay = get_param(setup, 'pause')
            pause_enabled = get_param(setup, 'pause', ENDI)
            pause_delay = get_param(setup, 'xepfd')
            an = self.an = duplex = pol = asymp = _1Gfull = _1Ghalf = _100Mfull = _100Mhalf = _10Mfull = _10Mhalf = NA
            interface_type = get_param(setup, 'xfpiface')
            
            nvp = \
            [
                ('Port ID', portID),
                ('Test Interface', interface),
                ('Interface Type', interface_type),
                ('Pause Enabled', pause_enabled),
                (Paragraph('<para><font>Pause Frame Delay (&#181;s)</font></para>', styleSheet['Normal']).getPlainText(), pause_delay),                    
           ]
        else:
            self.write_log('Bad Port Interface, Exiting', 'Error')
            return                 

        ports_config = []
        
        ports_config.append(nvp)
          
        port_table = []
        if format == 'pdf':
            makeTable = self.createPdfTable

            name_attached = False                
            
            for port_nvp in ports_config:
                i = 0    
                for n,v in port_nvp:
                    if not name_attached:
                        port_table.append([n,v])
                    else:
                        port_table[i].append(v)
                        i+=1
                name_attached = True                                        
                
        elif format == 'csv':
            makeTable = self.createCsvTable 

            name_attached = False                
            for port_nvp in ports_config:
                i = 0    
                for n,v in port_nvp:
                    if not name_attached:
                        port_table.append([n,v])
                    else:
                        port_table[i].append(v)
                        i+=1
                name_attached = True 
            
        makeTable(fd, 'Port Setup', port_table)    

    def eventTableFC(self, fd, params, format):
        event_des = {
            #notify
            'START_MEAS' : 'REC Start',
            'STOP_MEAS' : 'REC Stop',
            'LINK_UP' : 'Link Up',
            'LINK_DOWN' : 'Link Down',            
            'ERROR_HISTORY' : 'Error History',
            'NO_ERROR' : 'No Errors',
            #error
            'BIT' : 'Bit Error',
            'SYMBOL' : 'Symbol Error',
            'DISPARITY' : 'Disparity Error',
            'FC_SOF' : 'SOF Error',
            'FC_EOF' : 'EOF Error',
            'FCSCRC' : 'FCS/CRC Error',
            'NORDY' : 'NORDY Error',
            'OOSFRAME' : 'Out Of Sequence Frame Error',
            'LOSTFRAME' : 'Lost Frame Error',
            'DUPLICATEFRAME' : 'Duplicate Frame Error',
            'MSREI' : 'MS-REI Error',
            'HPREI' : 'HP-REI Error',
            'NO_BERT_TRAFFIC' : 'No Bert Traffic',
        }

        if params['event'] is None or params['event'][0] is None:
            self.write_log("No summary Event Table Data!")
            self.report_status == 'FAIL'
            return None
        
        totalpage = params['event']['totalpages']
        #count = params['events']['event']['count']
        table_name = 'Event Log'
        if format == 'pdf':
            num_events_per_page = 2 * page_size + 6 #total 36
            makeTable = self.createPdfTable
            header = ['Time:', 'Summary Events:']
            table = [header]
        else:
            makeTable = self.createCsvTable
            header = ["Summary Events:"]
            table = [header]

        if format == 'pdf' and params['event'][0]['event']['total'] > (num_events_per_page - 1) :
            fd.append(PageBreak())

        for num in range(0, totalpage):
          pageevent = params['event'][num]['event']
          inpagecount = pageevent['count']
          #print 'Inside Page Count', inpagecount
          for num2 in range(0, inpagecount):
             istream = 0
             ierror = 0
             strstream = ''
             strerror = ''
             beginend = ''
             stroutput = ''
             #print 'Testing second loop'
             event = pageevent['%d' % num2]
             #print 'time=>:', event['time']

             if event.has_key('stream'):
                 istream = event['stream']
             if event.has_key('gen_rel'):
                beginend = event['gen_rel']
             if event.has_key('count'):
                ierror = event['count']
                strerror = ' count:%d'%ierror                
             if istream != 0:
                strstream = ' Stream:%d'%istream
             evtype = event['evtype'];
             time = event['time'];
             layer = event['layer'];
             type = event['type'];                
             
             if type in event_des:
                 if evtype == 'NOTIFY':
                     if type in ['START_MEAS', 'STOP_MEAS']:
                         stroutput = event_des[type]
                     else:
                         stroutput = event_des[type] + ' ' + strstream
                 elif evtype == 'ERROR':
                     stroutput =  event_des[type] + ' '+ strerror +' ' + strstream                
                 table.append([event['time'],stroutput])
                 #print 'Event Table Data ==== >',stroutput
                 if format == 'pdf' and len(table) >= num_events_per_page:
                     makeTable(fd,table_name,table)
                     table_name = "Event Log Continued"
                     fd.append(PageBreak())
                     table = [header]  

        makeTable(fd,table_name,table)
        return   

    def eventTable(self, fd, params, format):
        event_des = {
            'START_MEAS' : 'REC Start',
            'STOP_MEAS' : 'REC Stop',
            'NO_BERT_TRAFFIC' : 'No Bert Traffic',
            'NO_ERROR' : 'No Errors',
            'ERROR_HISTORY' : 'Error History',
            'FCSCRC' : 'FCS/CRC Error',
            'IPCHECKSUM' : 'IP Checksum Error',
            'TCPCHECKSUM' : 'TCP Checksum Error',
            'UDPCHECKSUM' : 'UDP Checksum Error',
            'OOSFRAME' : 'Out Of Sequence Frame Error',
            'LOSTFRAME' : 'Lost Frame Error',
            'DUPLICATEFRAME' : 'Duplicate Frame Error',
            'BIT' : 'Bit Error',
            'B1' : 'B1 Error',
            'B2' : 'B2 Error',
            'B3' : 'B3 Error',
            'EVENT-LOP' : 'LOP',
            'EVENT-PAT-LOSS-BEGIN' : 'Pattern Loss Start',
            'EVENT-PAT-LOSS-END' : 'Pattern Loss End',
            'LINK_DOWN' : 'Link Down',
            'LINK_UP' : 'Link Up',
            'LOOP' : 'Looped',
            'PAT_LOSS':'Pattern Loss',
            'REMOTE_FAULT':'Remote Fault ',
            'LOCAL_FAULT':'Local Fault ',
            'SERV_DISRUPT':'Service Disruption ',
            'BEGIN':'Begin',
            'END':'End',
            'LOS':'LOS',
            'LOF':'LOF',
            'OOF':'OOF',
        }
        
        event_sonet_des = {
        'RSTIM': 'TIM-S',
        'MSAIS': 'AIS-L',
        'MSRDI': 'RDI-L',
        'AUAIS': 'AIS-P',
        'AULOP': 'LOP-P',
        'HPUNEQ':'UNEQ-P',
        'HPPLM': 'PLM-P',
        'HPRDI':'RDI-P',
        'HPTIM':'TIM-P',
        }
        
        stream_error = ['FCSCRC', 'IPCHECKSUM', 'TCPCHECKSUM', 'UDPCHECKSUM',
                        'OOSFRAME', 'LOSTFRAME', 'DUPLICATEFRAME', 'BIT']
        
        event_alarm = [
            ["PAT_LOSS",        "Pattern Loss",         "Pattern Loss"],
            ["REMOTE_FAULT",    "Remote Fault ",        "Remote Fault "],
            ["LOCAL_FAULT",     "Local Fault ",         "Local Fault "],
            ["SERV_DISRUPT",    "Service Disruption ",  "Service Disruption "],
            ["LOS",             "LOS",                  "LOS" ],
            ["LOF",             "LOF",                  "LOF"],
            ["OOF",             "OOF",                  "OOF"],
            ["RSTIM",           'RS-TIM',               'TIM-S'],
            ["MSAIS",           'MS-AIS',               'AIS-L'],
            ["MSRDI",           'MS-RDI',               'RDI-L'],
            ["AUAIS",           'AU-AIS',               'AIS-P'],
            ["AULOP",           'AU-LOP',               'LOP-P'],
            ["HPUNEQ",          'HP-UNEQ',              'UNEQ-P'],
            ["HPPLM",           'HP-PLM',               'PLM-P'],
            ["HPRDI",           'HP-RDI',               'RDI-P'], 
            ["HPTIM",           'HP-TIM',               'TIM-P'], 
            ["HPSRDI",          "HP-SRDI",              "SRDI-P"],
            ["HPCRDI",          "HP-CRDI",              "CRDI-P"],
            ["HPPRDI",          "HP-PRDI",              "PRDI-P"],
            ["TULOM",           "TU-LOM",               "LOM-V"],
            ["TULOP",           "TU-LOP",               "LOP-V"],
            ["TUAIS",           "TU-AIS",               "AIS-V"],
            ["LPRFI",           "LP-RFI",               "RFI-V"],
            ["LPRDI",           "LP-RDI",               "RDI-V"],
            ["LPSRDI",          "LP-SRDI",              "SRDI-V"],
            ["LPCRDI",          "LP-CRDI",              "CRDI-V"],
            ["LPPRDI",          "LP-PRDI",              "PRDI-V"],
            ["LPTIM",           "LP-TIM",               "TIM-V"],
            ["LPPLM",           "LP-PLM",               "PLM-V"],
            ["LPEPLM",          "LP-EPLM",              "EPLM-V"],
            ["LPELOM",          "LP-ELOM",              "ELOM-V"],
            ["LPUNEQ",          "LP-UNEQ",              "UNEQ-V"],
            ["HPTCUNEQ",        "HP-TCUNEQ",            "TCUNEQ-P"],
            ["HPTCLTC",         "HP-TCLTC",             "TCLTC-P"],
            ["HPTCAIS",         "HP-TCAIS",             "TCAIS-P"],
            ["HPTCRDI",         "HP-TCRDI",             "TCRDI-P"],
            ["HPTCODI",         "HP-TCODI",             "TCODI-P"],
            ["LPTCUNEQ",        "LP-TCUNEQ",            "TCUNEQ-V"],
            ["LPTCLTC",         "LP-TCLTC",             "TCLTC-V"],
            ["LPTCAIS",         "LP-TCAIS",             "TCAIS-V"],
            ["LPTCRDI",         "LP-TCRDI",             "TCRDI-V"],
            ["LPTCODI",         "LP-TCODI",             "TCODI-V"]
        ]

        event_error = [
            ["FCSCRC",          "FCS/CRC",              "FCS/CRC"],
            ["IPCHECKSUM",      "IP Checksum",          "IP Checksum"],
            ["TCPCHECKSUM",     "TCP Checksum",         "TCP Checksum"],
            ["UDPCHECKSUM",     "UDP Checksum",         "UDP Checksum"],
            ["OOSFRAME",        "Out Of Seq Frame",     "Out Of Seq Frame"],
            ["LOSTFRAME",       "Lost Frame",           "Lost Frame"],
            ["DUPLICATEFRAME",  "Duplicate Frame",      "Duplicate Frame"],
            ["BIT",             "BIT",                  "BIT"],
            ["B1",              "B1",                   "B1"],
            ["B2",              "B2",                   "B2"],
            ["B3",              "HP-B3",                "B3-P"],
            ["MSREI",           "MS-REI",               "REI-L"],
            ["HPREI",           "HP-REI",               "REI-P"],
            ["LPBIP",           "LP-BIP2",              "BIP2-V"],
            ["LPREI",           "LP-REI",               "REI-V"],
            ["AUPPJ",           "AU-PPJ",               "PPJ-P"],
            ["AUNPJ",           "AU-NPJ",               "NPJ-P"],
            ["AUNDF",           "AU-NDF",               "NDF-P"],
            ["TUPPJ",           "TU-PPJ",               "PPJ-V"],
            ["TUNPJ",           "TU-NPJ",               "NPJ-V"],
            ["TUNDF",           "TU-NDF",               "NDF-V"],
            ["FAS",             "FAS",                  "FAS"],
            ["CODE",            "CODE",                 "CODE"],
            ["HPTCIEC",         "HP-TCIEC",             "TCIEC-P"],
            ["HPTCREI",         "HP-TCREI",             "TCREI-P"],
            ["HPTCOEI",         "HP-TCOEI",             "TCOEI-P"],
            ["LPTCIEC",         "LP-TCIEC",             "TCIEC-V"],
            ["LPTCREI",         "LP-TCREI",             "TCREI-V"],
            ["LPTCOEI",         "LP-TCOEI",             "TCOEI-V"]
        ];
        
        event_noti = [
            ["LINK_UP",         "Link Up",              "Link Up"],
            ["LINK_DOWN",       "Link Down",            "Link Down"],
            ["START_MEAS",      "REC Start",            "REC Start"],
            ["STOP_MEAS",       "REC Stop",             "REC Stop"],
            ["NO_BERT_TRAFFIC", "No Bert Traffic",      "No Bert Traffic"],
            ["ERR_HISTORY",     "Error History",        "Error History"],
            ["NO_ERROR",        "No Errors",            "No Errors"]
       ]
            
        if params['event'] is None or params['event'][0] is None:
            self.write_log('No summary Event Table Data!')
            self.report_status == 'FAIL'
            return None

        isLP = self.isLP(params)
        isTU3 = self.isTU3(params)

        totalpage = params['event']['totalpages']
        self.write_log('Event total page = %d'%totalpage)
        table_name = 'Event Log'
        if format == 'pdf':
            style = [('BOX', (0, 0), (-1, 0), 1, colors.grey)]
            colwidths = [3.525 * inch, 3.525 * inch]
            num_events_per_page = 2 * page_size + 6 #total 36
            makeTable = self.createPdfTable
            header = ['Time:', 'Summary Events:']
            table = [header]
        elif format == 'csv':
            style = []
            colwidths = None
            makeTable = self.createCsvTable
            header = ["Summary Events:"]
            table = [header]

        if format == 'pdf' and params['event'][0]['event']['total'] > (num_events_per_page - 1) :
            fd.append(PageBreak())

        for num in range(0, totalpage):
            try:
                pageevent = params['event'][num]['event']
                inpagecount = pageevent['count']
                self.write_log('Event page=%d, count=%d'%(num, inpagecount))

                #print 'Inside Page Count', inpagecount
                for num2 in range(0, inpagecount):
                    istream = 0
                    ierror = 0
                    strstream = ''
                    strerror = ''
                    beginend = ''
                    stroutput = ''
                    #print 'Testing second loop'
                    event = pageevent['%d' % num2]
                    #print 'time=>:', event['time']
                    #self.write_log('RptgenEvt %s', event)
                    evtype = event['evtype'];
                    time = event['time'];
                    layer = event['layer'];
                    nw = 1;
                    if (layer == 'SONET'):
                        nw = 2;
                    type = event['type'];                
                    type_id = event['type_id']; 

                    if event.has_key('stream'):
                        istream = event['stream']
                    if event.has_key('gen_rel'):
                        beginend = event['gen_rel']
                    if event.has_key('count'):
                        ierror = event['count']
                        strerror = ' count:%d'%ierror                
                    if istream != 0:
                        strstream = ' Stream:%d'%istream
                    elif evtype == 'ERROR' and layer == 'ETHERNET' and type in stream_error:
                        strstream = ' Aggregate'
                        
                    is_event = True
                    if evtype == 'ALARM':
                        if type in ['PAT_LOSS','REMOTE_FAULT','LOCAL_FAULT','SERV_DISRUPT']:
                            stroutput = event_alarm[type_id][nw] + ' ' + event_des[beginend] + ' ' + strstream
                        elif type in ['LOS','LOF','OOF']:
                            stroutput = layer +' '+ event_alarm[type_id][nw] + ' ' + event_des[beginend] + ' ' + strstream
                        else:
                            stroutput = event_alarm[type_id][nw] + ' ' + event_des[beginend] + ' ' + strstream
                    elif evtype == 'NOTIFY':
                        if type in ['START_MEAS', 'STOP_MEAS']:
                            if type == 'STOP_MEAS' and event['savemode'] in ['LOW_BATTERY', 'HIGH_TEMPERATURE']:
                                if event['savemode'] == 'LOW_BATTERY':
                                    savemode = "Low Battery"
                                else:
                                    savemode = "High Temperature"
                                stroutput = event_noti[type_id][nw] + ' by ' + savemode
                            else :
                                stroutput = event_noti[type_id][nw]
                        else:
                            stroutput = event_noti[type_id][nw] + ' ' + strstream
                    elif evtype == 'ERROR':
                        if (nw == 1 and type_id == 13): # LP-BIP
                            if isTU3 == True:
                                stroutput = "LP-B3"  + ' '+ strerror +' ' + strstream
                            else:
                                stroutput = "LP-BIP2" + ' '+ strerror +' ' + strstream
                        else:
                            stroutput =  event_error[type_id][nw] + ' '+ strerror +' ' + strstream                
                    else:
                        is_event = False
                    if is_event:
                        table.append([event['time'],stroutput])
                        #print 'Event Table Data ==== >',stroutput
                        if format == 'pdf' and len(table) >= num_events_per_page:
                            makeTable(fd,table_name,table)
                            table_name = "Event Log Continued"
                            fd.append(PageBreak())
                            table = [header]
            except:
                self.write_log('', 'Error', sys.exc_info())

        makeTable(fd,table_name,table, style, colwidths)
        return
        
    def loopbackSetupFC(self, fd, config, format):

        try:
            setup = config['config']['ether']['stFCloopbackConfig']
        except:
            self.write_log('FC Loopback setup data not found!', 'Error')
            return

        loop_type = get_param(setup, 'looptype')
        loop_layer = get_param(setup, 'looplayer')
        
        if loop_type == 'MAN':
            loop_type = 'Manual'
        else:
            loop_type = 'Responder'

        if loop_layer == 'FC1':
           loop_layer = 'FC-1'
        else:
           loop_layer = 'FC-2'

        b2bOn = 'Off'
        if (get_param(setup, 'b2b_flag') != 0):
            b2bOn = 'On'

        nvp = \
            [
                ('Type',loop_type),
                ('Layer',loop_layer),
                ('DID','0x%.2X%.2X%.2X'%(setup['D_ID'][0],setup['D_ID'][1],setup['D_ID'][2])),
                ('SID','0x%.2X%.2X%.2X'%(setup['S_ID'][0],setup['S_ID'][1],setup['S_ID'][2])),
                ('B-TO-B Credit Management',b2bOn),
                ('B-TO-B Credit',get_param(setup, 'b2b_credit')),
            ]        

        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n,v in nvp:
                table.append( [n,v] )
        else:
            makeTable = self.createCsvTable
            table = nvp

        makeTable(fd, "Loopback Setup", table)
  
    def loopbackSetup(self, fd, config, format):
        try:
            setup = config['config']['ether']['stLoopbackConfig']
        except:
            self.write_log('Loopback setup data not found!', 'Error', sys.exc_info())
            return
       
        loop_type = get_param(setup, 'loop_type')
        loop_layer = get_param(setup, 'loop_layer')
        source_mac =  get_param(setup, 'source_mac')
        source_ip =  get_param(setup, 'source_ip', INA)
        if loop_type == 'MAN':
            loop_type = 'Manual'
        else:
            loop_type = 'Responder'
            
        if loop_layer == 'L1':
           loop_layer = 'Layer 1'
        else:
           loop_layer = 'Layer 2/3'
        nvp = \
            [
                ('Type',loop_type),
                ('Layer',loop_layer),
                ('MAC Source', source_mac),
                ('IP Source', source_ip),
            ]        
        table = []
        if format == 'pdf':
            makeTable = self.createPdfTable
            for n, v in nvp:
                table.append( [n,v] )
        else:
            makeTable = self.createCsvTable
            table = nvp
        makeTable(fd, "Loopback Setup", table)

        # VLAN Setup
        if format == 'pdf':
            makeTable = self.createPdfTable
        else:
            makeTable = self.createCsvTable
        vlans = setup['vlan']
        num_vlans = setup['nvlan']
        if num_vlans != 0:     
            table = self.getVlanTable(vlans, num_vlans)
            makeTable(fd, "Loopback VLAN Setup", table)

    def throughPutChart(self, lst, meas_data):
        try:
            events = meas_data['rfc2544_event']
            test = events[0]['event']
            results = meas_data['result_rfc2544']
        except:
            self.write_log('RFC2544 Througput chart data not found!', 'Error', sys.exc_info())
            return
        
        try:            
            is_throughput_on = results['is_throughput_on']
            if not is_throughput_on:
                self.write_log('Throuput must be ON!', 'Error')
                lst.append(Paragraph("No data available the chart is not displayed", styleSheet['BodyText']))
                return
        except:
           self.write_log('RFC2544 Througput chart data error!', 'Error', sys.exc_info())
           return

        try:            
            drawing = Drawing(400, 200)
            data = [[]]
            columns = []
    
            pageNo = 0
            total = get_param(events[pageNo]['event'], 'total')
            index = 0
            pos = 0
            while pos < total - 1:
                if index == page_size:
                    pageNo += 1
                    index = 0
                seq = events[pageNo]['event'][str(index)]
                if get_param(seq, 'testMode') != 0 or get_param(seq, 'testStage') != 0: 
                    index += 1
                    pos += 1
                    continue
    
                columns.append(str(get_param(seq, 'streamSize')))
                value = int(float(get_param(seq, 'passRate')))
                data[0].append(-2 if value == 0 else value)
                index += 1
                pos += 1
                    
            bc = VerticalBarChart()
            bc.x = 50
            bc.y = 50
            bc.height = 125
            bc.width = 300
            bc.data = data
            bc.strokeColor = colors.black
            bc.valueAxis.valueMin = -3
            bc.valueAxis.valueMax = 100
            bc.valueAxis.valueStep = 10
            bc.categoryAxis.labels.boxAnchor = 'ne'
            bc.categoryAxis.labels.dx = 8
            bc.categoryAxis.labels.dy = -2
            bc.categoryAxis.labels.angle = 30
            bc.categoryAxis.categoryNames = columns
            bc.barLabels.fontName = 'Helvetica'
            bc.bars[0].fillColor = colors.darkturquoise
            bc.bars[1].fillColor = colors.green
            bc.bars[2].fillColor = colors.red
            bc.bars[3].fillColor = colors.darksalmon
                
            drawing.add(bc)      
    
            header = 'Throughput Chart'
            lst.append(Paragraph(header, styleSheet['Heading2']))
                  
            lst.append(drawing)
            lst.append(Paragraph("Legend: Y axis = Frame Rate in percent, X axis = Frame Size", styleSheet['BodyText']))
        except:
            self.write_log('RFC2544 Througput chart generation error!', 'Error', sys.exc_info())
            return

    def frameLossChart(self, lst, meas_data):
        try:
            events = meas_data['rfc2544_event']
            test = events[0]['event']
            results = meas_data['result_rfc2544']
        except:
            self.write_log('RFC2544 frameLoss chart data not found!', 'Error', sys.exc_info())
            return
        
        try:            
            is_frameloss_on = results['is_frameloss_on']
            if not is_frameloss_on:
                self.write_log('frameloss must be ON!', 'Error')
                lst.append(Paragraph("No data available the chart is not displayed", styleSheet['BodyText']))
                return
        except:
            self.write_log('RFC2544 frameLoss chart data error!', 'Error', sys.exc_info())
            return

        try:            
            drawing = Drawing(400, 200)
            rates = []
            streams = []
            row = []
            data = []
            
            pageNo = 0
            total = get_param(events[pageNo]['event'], 'total')
            index = 0
            pos = 0
            while pos < total - 1:
                if index == page_size:
                    pageNo += 1
                    index = 0
                seq = events[pageNo]['event'][str(index)]
                if get_param(seq, 'testMode') != 2: 
                    index += 1
                    pos += 1
                    continue
                
                rate = get_param(seq, 'frameRate')
                if rate not in rates:
                    rates.append(rate)
                
                size = get_param(seq, 'streamSize')
                if size not in streams: 
                    streams.append(size)
                
                row.append(int(float(get_param(seq, 'frameLossRate'))))
                index += 1
                pos += 1
            
            col_max = 10
            col_count = len(rates)
            row_count = len(streams)
            rates = ['10', '20', '30', '40', '50', '60', '70', '80', '90', '100']       
            
            i = 0
            while i < (row_count + 2):            
                data.append([0] * col_max) # not * - deep array copy needed  
                i += 1
    
            index = 0
            for value in row:
                i = int(index / row_count)
                j = index - i * row_count + 1
                value = row[index]
                if value <= 0: value = -2
                try:
                    data[j][i] = value
                    print row_count, index, j, i, data[j][i]
                    index += 1
                except:
                    break
            
            i = 0
            while i < (row_count + 2):            
                data[i].reverse()
                i += 1
                    
            bc = VerticalBarChart()
            bc.x = 50
            bc.y = 50
            bc.height = 125
            bc.width = 300
            bc.data = data
            bc.strokeColor = colors.black
            bc.valueAxis.valueMin = -3
            bc.valueAxis.valueMax = 100
            bc.valueAxis.valueStep = 25
            bc.categoryAxis.labels.boxAnchor = 'ne'
            bc.categoryAxis.labels.dx = 8
            bc.categoryAxis.labels.dy = -2
            bc.categoryAxis.labels.angle = 30
            bc.categoryAxis.categoryNames = rates
            bc.bars[0].fillColor = colors.red
            bc.bars[1].fillColor = colors.red
            bc.bars[2].fillColor = colors.blue        
            bc.bars[3].fillColor = colors.green
            bc.bars[4].fillColor = colors.grey
            bc.bars[5].fillColor = colors.pink
            bc.bars[6].fillColor = colors.brown
            bc.bars[7].fillColor = colors.cyan
            bc.bars[8].fillColor = colors.lightgreen
            bc.bars[9].fillColor = colors.goldenrod
            bc.bars[10].fillColor = colors.lightcoral
            bc.bars[11].fillColor = colors.lightcoral
                
            drawing.add(bc)
            
            header = 'Frame Loss Chart'
            lst.append(Paragraph(header, styleSheet['Heading2']))
            lst.append(drawing)
            lst.append(Paragraph("Legend: Y axis = Frame Loss Rate in Percent, X axis = Frame Rate", styleSheet['BodyText']))
            lst.append(Paragraph("Bar Chart Colors for Frame Size in Bytes:", styleSheet['BodyText']))
        
            my_colors = ['red', 'blue', 'green', 'grey', 'pink', 'brown', \
                         'cyan', 'lightgreen', 'goldenrod', 'lightcoral']
            footnote = '<para>'
            for f_size, my_color in zip(streams, my_colors):
                footnote += '<font color=\'%s\'>%s</font> | ' % (my_color, f_size)
            footnote = footnote.rstrip(' | ')
            footnote += '</para>'
            lst.append(Paragraph(footnote,  styleSheet['BodyText']))
        except:
            self.write_log('RFC2544 frameLoss chart gereration error!', 'Error', sys.exc_info())
            return
        
    def myFirstPage(self, canvas, doc):
        canvas.saveState()
        canvas.setTitle(self.report_file_name)
        canvas.setFont(reportFont, 10)
        canvas.setLineWidth(.5)
        
        try:
            img = ImageReader(image_file)
            (w, h) = img.getSize()
            if (w, h) > (128, 64):
                canvas.drawImage(img, inch*0.85, PAGE_HEIGHT - 105, 128, 64)
            else:
                canvas.drawImage(img, inch*0.85, PAGE_HEIGHT - 105, w, h)
            isImage = True
        except:
            isImage = False
        if isImage == True:
            canvas.drawString(PAGE_WIDTH/2.65, PAGE_HEIGHT - 0.7 * inch, first_page_title)
            canvas.line(3 * inch, PAGE_HEIGHT-0.35 * inch, 3 * inch, PAGE_HEIGHT-120)
            canvas.line(5.6 * inch, PAGE_HEIGHT-0.35 * inch, 5.6 * inch, PAGE_HEIGHT-120)
            canvas.drawString(PAGE_WIDTH/2.65, PAGE_HEIGHT-68, '302.Enzo.Dr.')
            canvas.drawString(PAGE_WIDTH/2.65, PAGE_HEIGHT-80, 'San Jose, CA 95138 USA')
            canvas.drawString(PAGE_WIDTH/2.65, PAGE_HEIGHT-92, 'support@sunrisetelecom.com')
            canvas.drawString(PAGE_WIDTH/2.65, PAGE_HEIGHT-104, 'www.sunrisetelecom.com')
            canvas.drawString(PAGE_WIDTH/1.45, PAGE_HEIGHT-68, 'Date:  ' + self.reportDateTime)
            canvas.drawString(PAGE_WIDTH/1.45, PAGE_HEIGHT-80, 'Tel.    ' + '1 (408) 363-8000')
            canvas.drawString(PAGE_WIDTH/1.45, PAGE_HEIGHT-92, 'Fax    ' + '1 (408) 363-8313')
        else:
            canvas.drawString(inch, PAGE_HEIGHT-44, first_page_title)
            canvas.line(PAGE_WIDTH/2, PAGE_HEIGHT-0.35 * inch, PAGE_WIDTH/2, PAGE_HEIGHT-120)
            canvas.drawString(inch, PAGE_HEIGHT-68, '302.Enzo.Dr.')
            canvas.drawString(inch, PAGE_HEIGHT-80, 'San Jose, CA 95138 USA')
            canvas.drawString(inch, PAGE_HEIGHT-92, 'support@sunrisetelecom.com')
            canvas.drawString(inch, PAGE_HEIGHT-104, 'www.sunrisetelecom.com')
            canvas.drawString(PAGE_WIDTH/1.8, PAGE_HEIGHT-44, 'Date:  ' + self.reportDateTime)
            canvas.drawString(PAGE_WIDTH/1.8, PAGE_HEIGHT-68, 'Tel.    ' + '1 (408) 363-8000')
            canvas.drawString(PAGE_WIDTH/1.8, PAGE_HEIGHT-80, 'Fax    ' + '1 (408) 363-8313')
     
        canvas.line(0.61 * inch, PAGE_HEIGHT-0.35 * inch, PAGE_WIDTH - 0.61 * inch, PAGE_HEIGHT-0.35 * inch)
        canvas.line(0.61 * inch, PAGE_HEIGHT-120, PAGE_WIDTH - 0.61 * inch, PAGE_HEIGHT-120)
        canvas.line(0.61 * inch, PAGE_HEIGHT-0.35 * inch, 0.61 * inch, PAGE_HEIGHT-120)
        canvas.line(PAGE_WIDTH - 0.61 * inch, PAGE_HEIGHT-0.35 * inch, PAGE_WIDTH - 0.61 * inch, PAGE_HEIGHT-120)
        canvas.setFont(reportFont, 8)
        canvas.drawString(0.61 * inch, 0.35 * inch, "%s" % (pageinfo))
        canvas.restoreState()
    
    def myLaterPages(self, canvas, doc):
        canvas.saveState()
        canvas.setFont(reportFont, 8)
        canvas.drawString(0.61 * inch, 0.35 * inch, "%s" % (pageinfo))
        canvas.restoreState()

   
#
# Formatting functions and constants
#

def CSV_NAME(name): return "%s" % name

NA = 'N/A'      # default 
NNA = 0         # for numeric
FNA = 0.00      # for decimals
MNA = '00-00-00-00-00-00' # for MAC
INA = '0.0.0.0' # for IP
NYNA = 'No'
CNA = '0.00'    # for part number format like 127,234,453.10
ICNA = 'X,XXX'  # for currency format for int or long 127.234.453
ENDI = 'Disable' # Disable/Enable
ITS = 'CCC'       # for string from int
NHEX = '0x%X'     # hex format
EXP = '%.*G'      # 5.4E-4, exponent display
dummy_list = [NA, NNA, FNA, MNA, INA, NYNA, CNA, ENDI] # to be continue...
def get_param(dic, param_name, defval = NA, get_str=True):
    value = defval
    try: value = dic[param_name]
    except: return value
    # base
    if isinstance(value, str) or isinstance(value, unicode):
        return value
    # ip
    if defval == INA:
        return int_to_ip(value)
    # No Yes
    if defval == NYNA:
        return ['No', 'Yes'][int(value)]
    
    if defval == ENDI:
        return ['Disable', 'Enable'][int(value)]

    if defval == ITS:
        return int_to_string(value)

    if defval == NHEX:
        return int_to_hex(value, get_str)
    
    # floats and currency-like numbers
    if isinstance(value, float) and defval == EXP:
        return exponet_to_string(value, get_str)
    
    if isinstance(value, (int, long)) and defval == ICNA:
        return  curnum_to_string(value, get_str)

    if isinstance(value, float) or defval == CNA:
        #if value == FNA and defval != NA: return defval
        try:
            value = float(value)
        except: 
            return CNA
        #if value > 0.0 and value < 0.01: return '< 0.01'
        return fmt_float(value, get_str)

    # base
    if isinstance(value, (int, long)):
        if value == NNA and defval != NA: return defval
        return value
    # MAC
    if type(value) is types.ListType:
        if len(value) == 6:
            tmp = '%02X-%02X-%02X-%02X-%02X-%02X' % tuple(value) # hex format
            return tmp.replace(' ', '0')
        elif len(value) == 4:
            return '%d.%d.%d.%d' % tuple(value)
        else:
            return str(value)
        
    # unknown - error
    print 'Error: Unknown param type for value: "%s" (%s)!!!' % (value, type(value))
    return defval

def get_param_float(dictionary, param, default='N/A', precision=2):
    if param == 'dummy':
        return default
    else:            
        try:                
            value = dictionary[param]                                                
            if isinstance(value,float):
                if default == EXP:
                    value = "%.*G" % (precision,value)
                    if value == "0E0":
                        value = default
                elif precision == 0:
                    value = int(value)
                else:
                    if value == 0.0:
                        value = 0
                    else:
                        value = "%.*f" % (precision,value)
        except Exception, e:
            value = default                
            self.log.error("get_float_param(): %s -- %s"%(sys.exc_info()[0],e))  
            
            if '_' in dictionary:
                self.log.debug("Dictionary (%s) has not have attribute: %s"%(dictionary['_'],param))
            else:            
                self.log.debug("Dictionary does not have attribute: %s"%param)
        return value

def get_param_float_fc(dictionary, param, default='N/A', precision=2):
    if param == 'dummy':
        return default
    else:            
        try:                
            value = dictionary[param]                                                
            if isinstance(value,float):
                if default == '0E0':
                    value = "%.*G" % (precision,value)
                    if value == "0":
                        value = default
                elif precision == 0:
                    value = int(value)
                else:
                    value = "%.*f" % (precision,value)
        except Exception, e:
            value = default                
            self.log.error("get_float_param(): %s -- %s"%(sys.exc_info()[0],e))  
            
            if '_' in dictionary:
                self.log.debug("Dictionary (%s) has not have attribute: %s"%(dictionary['_'],param))
            else:            
                self.log.debug("Dictionary does not have attribute: %s"%param)
        return value

def fmt_float(value, to_str=True):
    val = round(value + 0.0005, 2)
    if to_str: 
        return locale.format('%.2f', val, True)
    else: 
        return val
 
def fmt_float3(value, to_str=True):
    val = round(value + 0.00005, 3)
    if to_str: 
        return locale.format('%.3f', val, True)
    else: 
        return val

def fmt_float_pre(value, precision, to_str=True):
    val = round(value + 0.05*precision, precision)
    if to_str: 
        val = "%.*f" % (precision,value)
    return val

def fmt_floate(value):
    e = 0
    if value < 0.05:
        while value < 1.0:
            value = float(value) * 10
            e += 1
            val = str(round(value + 0.00005, 3)) + 'E-' + str(e)
    else: val = value
    return val
   
def exponet_to_string(value, to_str=True):
    if to_str: 
        if value == FNA :
            return '0.00E0'
        else:
            return '%.*G'%(3,float(value))
    else: 
        return value

def exponet3_to_string(value, to_str=True):
    if to_str: 
        if value == FNA :
            return '0.000E+00'
        else:
            return '%.*E'%(3,float(value))
    else: 
        return value
    
exp3tostr = exponet3_to_string

def curnum_to_string(value, to_str=True):
    if to_str: 
        return locale.format('%d', value, True)
    else: 
        return value

curtostr = curnum_to_string

def int_to_hex(value, width=1, to_str=False):
    if to_str: 
        if isinstance(value, (int, long)):                                                
            return '0x%0*X'%(width, value)
        else:
            return 'N/A'
    else:
        return value
    
def fbps(fstr, fval):
    return (fstr % fbps_pref(fval), fbps_val(fval))

def trunkzerodeciaml(value):
    try:
        x = value.find('.')
        decimal = int(value[x+1:len(value)])
        if decimal == 0:
            value = value[0:x]
    except:
        pass
    return value

    
def fbps(fstr, fval):
    return (fstr % fbps_pref(fval), fbps_val(fval))

def fbps4(fstr, fval1, fval2, flag = None):
    if fval1 in dummy_list:
        val1 = fval1
        name, val2 = fbps(fstr, fval2)
    elif fval2 in dummy_list:
        name, val1 = fbps(fstr, fval1)
        val2 = fval2
    else:    
        name = fstr % fbps_pref(fval1, fval2)
        val1, val2 = fbps_val(fval1, fval2)    
    
    # When value is 0.0, then remove decimal value
    val1 = trunkzerodeciaml(val1)
    val2 = trunkzerodeciaml(val2)

    if flag is None:
       return name, val1, val2    
    return name, val1, val2, flag
    
def fbps_pref(bps, bps2 = None):
    return 'kbps'
    # old formating
    res = 'error'
    try:
        if bps2 is not None: val = min(float(bps), float(bps2))
        else: val = float(bps)
        if val > 1000000.0: res = 'Mbps'
        elif val > 1000.0: res = 'kbps'
        else: res = 'bps'
    except: pass
    return res

def fbps_val(bps, bps2 = None):
    res1 = CNA
    try:
        res1 = float(bps) / 1.0
    except:
        print 'Error parse value "%s" to float!' % bps
        if bps2 is not None:
            return res1, res1
        else:
            return res1
    if bps2 is not None:
        try:
            res2 = float(bps2) / 1.0
        except:
            print 'Error parse value "%s" to float!' % bps2
            return res1, res1
        return (fmt_float(res1, True), fmt_float(res2, True))
    else:
        return fmt_float(res1, True)
    
    # old formating
    res1 = NA
    try:
        if bps2 is not None: 
            val1 = float(bps)
            val2 = float(bps2)
            val = min(val1, val2)
        else: 
            val = float(bps)
            val1 = val
            val2 = 0
        
        if val > 1000000.0: 
            res1 = val1 / 1000000.0
            res2 = val2 / 1000000.0
        elif val > 1000.0: 
            res1 = val1 / 1000
            res2 = val2 / 1000
        else:
            res1 = val1
            res2 = val2
    except: 
        return res1
    
    if bps2 is not None:
        return '%.2f' % round(res1, 2), '%.2f' % round(res2, 2)
    return '%.2f' % round(res1, 2)

def int_to_ip (intip):
        octet = ''
        for exp in [3, 2, 1, 0]:
                octet = octet + str(intip / ( 256 ** exp )) + "."
                intip = intip % ( 256 ** exp )
        return (octet.rstrip('.'))

def int_to_string (vallist):
    s = "";
    for val in vallist:
        if val == 0:
            break
        s += chr(val);
    return s
    
def get_param_from_path(dic, param_path, param_name, defval = NA, get_str=True):
    targed = dic
    if param_path != '':
        try:
            for node in param_path.split('/'):
                targed = targed[node]
        except: pass
    return get_param(targed, param_name, defval, get_str)

def altbin(n):
    val = n
    if n < 0:
        return '0'
    s = ''
    while n != 0:
        if n % 2 == 0:
            bit = '0'
        else: 
            bit = '1'
        s = bit + s
        n >>= 1
    return s  

def binary(n, digits=8):
    return altbin(n).rjust(digits, '0')

def setDDHHMMSS(sec, showday=True):
    """ 
    make a string of digits "dd hh:mm:ss"
    """
    if (showday):
        dd = sec/86400;
    hh = (sec/3600)%24;
    mm = (sec%3600)/60;
    ss = (sec%60);
    timetext = "%02d %02d:%02d:%02d"%(dd, hh, mm, ss)
    return timetext;

#
# Internal classes
#

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 8)
        self.drawRightString(PAGE_WIDTH - 0.61 * inch, 0.35 * inch,
            "Page %d of %d" % (self._pageNumber, page_count))

# variables used for PDF generation
reportFont = 'Helvetica'
reportEncoding = 'WinAnsiEncoding'
dataFontType = 'Times-Roman'
titleFontSize = 14
headerFontSize = 12
dataFontSize = 10
titleSpacing = 40
headerSpacing = 30
dataSpacing = 15
indent = 100
dataIndent = 180
dataIndent2 = 20
endOfPage = 100

# Platypus page layout system variables for PDF generation
PAGE_HEIGHT=defaultPageSize[1]
PAGE_WIDTH=defaultPageSize[0]
styles = getSampleStyleSheet()
first_page_title = "Sunrise Telecom Inc."
pageinfo = "Tested with RxT-TEN - www.sunrisetelecom.com"
image_file = '/usr/local/module/rxt10gx/Sunrise/daemon/logo.gif'


if __name__ == '__main__':
    debug = False 
    arg = sys.argv[1:]
    if len(arg)>0:
        debug = arg[0] == "debug"
    repGen = reportGenerator(debug)
    repGen.run()
else:
    print 'reportGenerator.py: Invoked by other module'
