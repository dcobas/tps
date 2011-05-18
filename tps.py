#!   /usr/bin/env   python
#    coding: utf8

import sys
import cmd
import glob
import os, os.path
import datetime

from ConfigParser import ConfigParser
from optparse import OptionParser
from hashlib import sha1 as sha160
from tpsexcept import *

default_config_file = 'default.cfg'

class Suite(object):
    def __init__(self, cfgfilename=default_config_file):
        self.config = cfgfilename
        self.path = './tests'
        self.logpath = './logs'
        self.pattern = 'test[0-9][0-9]'
        self.log_pattern = 'output_%(serial)s_%(timestamp)s_%(test)s.txt'

    def read_config(self):
        try:
            cfg = file(self.config).read()
        except IOError:
            errmsg = 'could not read configuration file {0}'
            errmsg = errmsg.format(self.config)
            raise TpsCritical(errmsg)
        config = ConfigParser(cfg)

        self.path        = config.get('files',  'path')
        self.logpath     = config.get('files',  'logs')
        self.pattern     = config.get('files',  'pattern')
        self.log_pattern = config.get('files',  'log_pattern')

    def run(self):
        ts = timestamp()
        test_glob = os.path.join(self.path, self.pattern + '.py')
        sequence = glob.glob(test_glob)
        if self.path not in sys.path:
            sys.path.append(self.path)
        for test in sequence:
            testname, ext = os.path.splitext(os.path.basename(test))
            serial = get_serial()
            ts = timestamp()
            logname = os.path.join(self.logpath, self.log_pattern % dict(
                    serial=serial, timestamp=ts, test=testname))
            tmpout = sys.stdout
            with open(logname, 'w') as sys.stdout:
                try:
                    mod = __import__(testname, globals(), locals(), ['main'])
                    mod.main()
                except TpsCritical, e:
                    print 'Tps Critical error, aborting: [%s]' % e.message
                    break
                except TpsError, e:
                    print 'Tps Error error, continuing: [%s]' % e.message
                except TpsUser, e:
                    print 'Tps User error, user intervention required: [%s]' % e.message
                    print 'Error %s found in test named %s. ',
                    while True:
                        ans = raw_input('Abort or Continue? (A/C) ')
                        ans = ans.lower()
                        if ans in ('a', 'c'):
                            break
                    if ans == 'a':
                        break
                    elif ans == 'c':
                        continue
                except TpsWarning, e:
                    print 'Tps Warning: [%s]' % e.message
                finally:
                    print 'ran test ', test
                    pass
            sys.stdout = tmpout

    def write_config(self):
        config = ConfigParser()

        config.add_section('global')
        config.set('global', 'timestamp', timestamp())
        config.set('global', 'sha', sha('3.14'))
        config.add_section('files')
        config.set('files', 'path', self.path)
        config.set('files', 'logs', self.logpath)
        config.set('files', 'pattern', self.pattern)
        config.set('files', 'log_pattern', self.log_pattern)

        # Writing our configuration file
        with open(self.config, 'wb') as configfile:
            config.write(configfile)

def get_serial():
    """return serial number of current board to test
    """
    return sha(timestamp())

def timestamp():
    """timestamp for now
    """
    return datetime.datetime.now().strftime('%Y%m%d.%H%M%S%f')

def sha(blob, len=7):
    """create a sha-160 hash of a binary object

    len is the number of hex digits to take from the hex digest,
    defaulting to 7 just as in git
    """

    hash = sha160(blob)
    ret = hash.hexdigest()
    if len:
        return ret[:len]

class Cli(cmd.Cmd):
    def __init__(self, suite):
        # Suite instance manipulated by this cli
        self.suite = suite
        cmd.Cmd.__init__(self)

    def do_board(self, arg):
        if arg:
            self.suite.board = arg
        else:
            print self.suite.board

    def do_serial(self, arg):
        if arg:
            self.suite.serial = arg
        else:
            print self.suite.serial

    def do_path(self, arg):
        if arg:
            self.suite.path = arg
        else:
            print self.suite.path

    def do_run(self, arg):
        pass
    def do_repeat(self, arg):
        pass

    def do_save(self, arg):
        self.suite.write_config()

    def do_log(self, arg):
        if arg:
            self.suite.log = arg
        else:
            print self.suite.log

    def do_log_path(self, arg):
        if arg:
            self.suite.log_path = arg
        else:
            print self.suite.log_path

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

    (options, args) = parser.parse_args()

    s = Suite(options.config)
    s.write_config()
    s.run()

def main2():
    cli = Cli()
    cli.cmdloop()

if __name__ == '__main__':
    main2()
