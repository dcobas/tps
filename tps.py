#!   /usr/bin/env   python
#    coding: utf8

import sys
import cmd
import glob
import re
import os, os.path
import datetime

from ConfigParser import ConfigParser
from optparse import OptionParser
from hashlib import sha1 as sha160
from tpsexcept import *
from pprint import pprint

default_config_file = 'default.cfg'
default_log_pattern = 'test_%(board)s_%(serial)s_%(number)s_%(timestamp)s.txt'

def run_test(testname, logname):
    """run test testname with output redirected to logname
    """
    try:
        tmpout = sys.stdout
        with open(logname, 'w') as sys.stdout:
            mod = __import__(testname, globals(), locals(), [])
            mod.main()
    except:
        raise
    finally:
        sys.stdout = tmpout

class Suite(object):
    def __init__(self, cfgfilename=default_config_file):
        self.config       =  default_config_file
        self.log_pattern  =  default_log_pattern
        self.required     =  [ 'board', 'serial', 'test_path',
                                'log_path', 'log_name', 'sequence' ]
        for fieldname in self.required:
            self.__setattr__(fieldname, None)

    def missing(self):
        """report missing fields before suite run"""

        missing = [ fieldname for fieldname in self.required
                if self.__getattribute__(fieldname) is None ]
        return missing

    def read_config(self):
        try:
            cfg = file(self.config).read()
        except IOError:
            errmsg = 'could not read configuration file {0}'
            errmsg = errmsg.format(self.config)
            raise TpsCritical(errmsg)
        config = ConfigParser(cfg)

        self.board       = config.get('global', 'board')
        self.serial      = config.get('global', 'serial')
        self.path        = config.get('files',  'test_path')
        self.logpath     = config.get('files',  'log_path')
        self.pattern     = config.get('files',  'log_name')
        self.log_pattern = config.get('files',  'log_pattern')

    def write_config(self):
        config = ConfigParser()

        config.add_section('global')
        config.add_section('files')

        config.set('global', 'board', self.board)
        config.set('global', 'serial', self.serial)
        config.set('files',  'path', self.path)
        config.set('files',  'logs', self.logpath)
        config.set('files',  'pattern', self.pattern)
        config.set('files',  'log_pattern', self.log_pattern)

        # Writing our configuration file
        with open(self.config, 'wb') as configfile:
            config.write(configfile)

    def run(self):
        ts = timestamp()
        if not self.serial:
            serial = get_serial()
        else:
            serial = self.serial
        runid = sha(self.board + ':' + serial + ':' + ts)
        logfilename = self.log.format(self.board, serial, ts, runid)
        logfilename = os.path.join(self.logpath, logfilename)
        log = file(logfilename, 'wb')
        test_glob = os.path.join(self.path, self.pattern + '.py')
        sequence = glob.glob(test_glob)

        if self.path not in sys.path:
            sys.path.append(self.path)

        log.write('test run\n'
            '    board      = {0}\n'
            '    serial     = {1}\n'
            '    timestamp  = {2}\n'
            '    runid      = {3}\n'.format(
                self.board, self.serial, ts, runid))
        for test in sequence:
            try:
                testname = os.path.splitext(os.path.basename(test))[0]
                shortname= re.match('test(\d\d)', testname).group(1)
                logname  = self.log_pattern % dict(serial=serial, timestamp=ts, test=testname)
                logname  = os.path.join(self.logpath, logname)
                log.write('------------------------\n')
                log.write('running test {0} = {1}\n'.format(shortname, test))
                run_test(testname, logname)
            except TpsCritical, e:
                print 'test [%s]: critical error, aborting: [%s]' % (shortname, e.message)
                log.write('    critical error in test {0}, exception [{1}]\n'.format(shortname, e.message))
                log.write('    cannot continue, aborting test suite')
                break
            except TpsError, e:
                print 'test [%s]: error, continuing: [%s]' % (shortname, e.message)
                log.write('    error in test {0}, exception [{1}]\n'.format(shortname, e.message))
            except TpsUser, e:
                print 'test [%s]: user error, user intervention required: [%s]' % (shortname, e.message)
                log.write('    error in test {0}, exception [{1}]\n'.format(shortname, e.message))
                while True:
                    ans = raw_input('Abort or Continue? (A/C) ')
                    ans = ans.lower()
                    if ans in ('a', 'c'):
                        break
                if ans == 'a':
                    log.write('    user intervention: abort\n')
                    break
                elif ans == 'c':
                    log.write('    user intervention: continue\n')
                    continue
            except TpsWarning, e:
                print 'test [%s]: warning: [%s]' % (shortname, e.message)
                log.write('    warning in test {0}, exception [{1}]\n'.format(shortname, e.message))
            else:
                log.write('    OK\n')
            finally:
                log.write('finished test {0}\n'.format(test))
                pass
        log.close()

def get_serial():
    """return serial number of current board to test
    """
    return raw_input('board serial number? ').strip()

def timestamp():
    """timestamp for now
    """
    return datetime.datetime.now().strftime('%Y%m%d.%H%M%S.%f')

def sha(blob, len=7):
    """create a sha-160 hash of a binary object

    len is the number of hex digits to take from the hex digest,
    defaulting to 7 just as in git
    """

    hash = sha160(blob)
    ret = hash.hexdigest()
    if len:
        return ret[:len]

class Cli(cmd.Cmd, Suite):
    def __init__(self, cfgfilename=default_config_file):
        cmd.Cmd.__init__(self)
        Suite.__init__(self, cfgfilename)

    def do_board(self, arg):
        if arg:
            self.board = arg
        else:
            print self.board

    def do_serial(self, arg):
        if arg:
            self.serial = arg
        else:
            print self.serial

    def do_path(self, arg):
        if arg:
            self.path = arg
        else:
            print self.path

    def do_run(self, arg):
        pass
    def do_repeat(self, arg):
        pass

    def do_save(self, arg):
        self.write_config()

    def do_log(self, arg):
        if arg:
            self.log = arg
        else:
            print self.log

    def do_log_path(self, arg):
        if arg:
            self.log_path = arg
        else:
            print self.log_path

    def do_EOF(self, arg):
        print
        return True

    def do_quit(self, arg):
        return True

def main1():
    parser = OptionParser()
    parser.add_option("-c", "--config", dest="config",
                        default=default_config_file,
                        help="config file name", metavar="FILE")
    parser.add_option("-s", "--serial", dest="serial",
                        default='000000',
                        help="board serial number", metavar="FILE")

    (options, args) = parser.parse_args()

    s = Suite(options.config)
    if options.serial:
        s.serial = options.serial
    s.write_config()
    s.run()

def main2():
    s = Suite()
    cli = Cli()
    cli.cmdloop()

if __name__ == '__main__':
    main1()
