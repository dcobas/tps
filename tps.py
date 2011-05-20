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

default_config_file  = 'tpsdefault.cfg'
default_log_pattern  = 'tps_%(board)s_%(serial)s_%(number)s_%(timestamp)s.txt'
default_log_name     = 'tps_run_{0}_{1}_{2}_{3}.txt'
default_test_pattern = 'test[0-9][0-9]'

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

        self.required     =  [ 'board', 'serial', 'test_path',
                                'log_path', 'sequence' ]
        for fieldname in self.required:
            self.__setattr__(fieldname, None)
        self.config       =  default_config_file
        self.log_pattern  =  default_log_pattern
        self.log_name     =  default_log_name

    def missing(self):
        """report missing fields before suite run"""

        missing = [ fieldname for fieldname in self.required
                if self.__getattribute__(fieldname) is None ]
        return missing

    def read_config(self, name=None):
        if name:
            self.config = name
        try:
            cfg = file(self.config).read()
        except IOError:
            errmsg = 'could not read configuration file {0}'
            errmsg = errmsg.format(self.config)
            raise TpsCritical(errmsg)
        config = ConfigParser(cfg)

        self.board        =  config.get('global', 'board')
        self.serial       =  config.get('global', 'serial')
        self.test_path    =  config.get('global', 'test_path')
        self.log_path     =  config.get('global', 'log_path')
        self.log_name     =  config.get('global', 'log_name')
        self.log_pattern  =  config.get('global', 'log_pattern')

    def write_config(self):
        config = ConfigParser()

        config.add_section('global')

        config.set('global', 'board', self.board)
        config.set('global', 'serial', self.serial)
        config.set('global', 'test_path', self.test_path)
        config.set('global', 'log_path', self.log_path)
        config.set('global', 'log_name', self.log_name)
        config.set('global', 'log_pattern', self.log_pattern)

        # Writing our configuration file
        with open(self.config, 'wb') as configfile:
            config.write(configfile)

    def run(self):
        ts = timestamp()
        missing = self.missing()
        if missing:
            print 'cannot run with missing parameters,',
            print 'please supply:',
            for f in missing:
                print f,
            print
            return
        runid = sha(self.board + ':' + self.serial + ':' + ts)
        logfilename = self.log_name.format(self.board, self.serial, ts, runid)
        logfilename = os.path.join(self.log_path, logfilename)
        log = file(logfilename, 'wb')
        test_glob = os.path.join(self.test_path, default_test_pattern + '.py')
        sequence = glob.glob(test_glob)

        if self.test_path not in sys.path:
            sys.path.append(self.test_path)

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
                logname  = self.log_pattern % dict(board=self.board,
                                serial=self.serial, timestamp=ts,
                                number=shortname)
                logname  = os.path.join(self.log_path, logname)
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
        self.ruler = ''

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

    def do_test_path(self, arg):
        if arg:
            self.test_path = arg
        else:
            print self.test_path

    def do_log_path(self, arg):
        if arg:
            self.log_path = arg
        else:
            print self.log_path

    def do_save(self, arg):
        self.write_config()

    def do_run(self, arg):
        pass
    def do_repeat(self, arg):
        if arg:
            try:
                self.repeat = int(arg)
            except ValueError:
                print arg, 'is not an integer'
        else:
            print self.repeat


    def do_EOF(self, arg):
        print
        return True

    def do_quit(self, arg):
        "exit cli"
        return True

    def do_show(self, arg):
        "show current configuration of suite"

        params_to_list = (
            'board',
            'serial',
            'test_path',
            'log_path',
            'repeat',
            'random', )
        for param in params_to_list:
            if param in self.__dict__:
                print '%-12s' % (param + ':'),
                print self.__getattribute__(param)

    do_q = do_quit
    do_h = cmd.Cmd.do_help

def main1():
    usage = '%prog: [options] test ...'
    parser = OptionParser(usage)
    parser.add_option("-c", "--config", dest="config",
                        default="tpsdefault.cfg",
                        help="config file name")
    parser.add_option("-C", "--cli", dest="cli", action="store_true",
                        help="enter command-line interpreter")
    parser.add_option("-b", "--board", dest="board",
                        help="board name (e.g. -b SPEC)", metavar="NAME")
    parser.add_option("-s", "--serial", dest="serial",
                        help="board serial number", metavar="SERIAL")
    parser.add_option("-t", "--test-path", dest="test_path",
                        help="path to test files", metavar="PATH")
    parser.add_option("-l", "--log-path", dest="log_path",
                        help="path to log files", metavar="PATH")
    parser.add_option("-n", "--ntimes", dest="repeat",
                        help="number of times to repeat the batch of tests",
                        metavar="NUMBER")
    parser.add_option("-r", "--randomize", action="store_true",
                        help="run the batch in random order", )

    (options, args) = parser.parse_args()

    s = Cli(options.config)
    s.__dict__.update(options.__dict__)
    s.sequence = args
    if options.cli:
        s.cmdloop()
    else:
        s.run()

def main2():
    s = Suite()
    cli = Cli()
    cli.cmdloop()

if __name__ == '__main__':
    main1()
