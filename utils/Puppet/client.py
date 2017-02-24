#!/usr/local/bin/python2.7
# encoding: utf-8
'''
client -- The entry for the environment checking and setup software

client is a collection for check whether PD3 software can be deploy on the environment.

It defines entry for calling checking and setup interace

@author:     Hanxm
        
@copyright:  2014 organization_name. All rights reserved.
        
@license:    license

@contact:    user_email
@deffield    updated: Updated
'''

import sys
import os

import DebugLog
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from server_check import Server_Check
from Software_Install import Software_Install
from ErrorHandler import WrongVersionNumber_Error

__all__ = []
__version__ = 0.1
__date__ = '2014-12-15'
__updated__ = '2014-12-15'

DEBUG = 0
TESTRUN = 0
PROFILE = 0

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''
    
    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    #program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_shortdesc = "Command line options"
    program_license = '''%s

  Created by user_name on %s.
  Copyright 2014 organization_name. All rights reserved.
  
  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0
  
  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument("-i", "--install", dest="only_install", action='store_true', help="only execute install actions")
        parser.add_argument("-2.5", "--installpd2.5", dest="installpd2_5", action='store_true', help="install pd2.5")
        parser.add_argument("-2.6", "--installpd2.6", dest="installpd2_6", action='store_true', help="install pd2.6")
        parser.add_argument("-3.0", "--installpd3", dest="installpd3", action='store_true', help="install pd3")
        parser.add_argument("-xeap", "--installxeap", dest="installxeap", action='store_true', help="install xeap")
        parser.add_argument(dest="server_ip", help="The server's ip address", metavar="server_ip")
        parser.add_argument(dest="password", help="The server's user password", metavar="password")
        parser.add_argument(dest="versionnumber", help="The package's version number", metavar="versionnumber")
        
        # Process arguments
        args = parser.parse_args()
        
        verbose = args.verbose
        server_ip = args.server_ip
        password = args.password
        versionnumber = args.versionnumber

        os.environ["PACKAGE_VERSION_NUMBER"] = versionnumber
        
        only_install = args.only_install
        installpd2_5 = args.installpd2_5
        installpd2_6 = args.installpd2_6
        installpd3 = args.installpd3
        installxeap = args.installxeap
        
        if verbose > 0:
            DEBUG = 1
            DebugLog.is_verbose = True
            if 1 == verbose:
                DebugLog.loglevel1 = True
            elif 2 == verbose:
                DebugLog.loglevel1 = True
                DebugLog.loglevel2 = True
            
        DebugLog.init_log(DebugLog.is_verbose)
        DebugLog.info_print("Verbose mode on")
        
        if not server_ip:
            raise CLIError("There should be server'ip in the command line.")
        else:
            print "The server ip is %s" % server_ip
        
        #remote_target_session = 
        server_check = Server_Check(server_ip, password, with_config=False)
        
        if not only_install:
            server_check.check_server_environment()
            
        if installpd2_5:
            if not versionnumber.startswith("2.5"):
                raise WrongVersionNumber_Error("2.5")
            server_check.assert_AIX_os()
            server_check.check_root_disk_size("3G")
            Software_Install(server_ip, password).install_pd25()
        elif installpd2_6:
            if not versionnumber.startswith("2.6"):
                raise WrongVersionNumber_Error("2.6")
            server_check.assert_AIX_os()
            server_check.check_root_disk_size("10G")
            Software_Install(server_ip, password).install_pd26()
        elif installpd3:
            if not versionnumber.startswith("3.0"):
                raise WrongVersionNumber_Error("3.0")
            server_check.assert_Linux_os()
            server_check.check_root_disk_size("5G", AIX=False)
            Software_Install(server_ip, password).install_pd3()
        elif installxeap:
            #if not versionnumber.startswith("1.0"):
            #    raise WrongVersionNumber_Error("1.0")
            server_check.assert_Linux_os()
            server_check.check_root_disk_size("5G", AIX=False)
            Software_Install(server_ip, password).install_xeap()

        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception, e:
#         if DEBUG or TESTRUN:
#             raise(e)
        
        if DebugLog.loglevel1 and not DebugLog.loglevel2:
            raise(unicode(e))
        
        if DebugLog.loglevel2:
            import traceback,pdb
            traceback.print_stack()
            #traceback.print_last()
            pdb.post_mortem()
            
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + str(e) + "\n")
        try:
            sys.stderr.write(indent + "  " + unicode(e) + "\n")
        except:
            pass
        sys.stderr.write(indent + "  for help use --help")
        return 2

if __name__ == "__main__":
    if DEBUG:
        #sys.argv.append("-h")
        sys.argv.append("-v")

    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'client_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())
