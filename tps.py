#!   /usr/bin/env   python
#    coding: utf8

import sys
import cmd
import glob
import re
import os, os.path
import stat
import datetime
import random
import warnings

from ConfigParser import ConfigParser, NoOptionError
from optparse import OptionParser
from sha import sha as sha160
from tpsexcept import *

default_config_file  = 'tpsdefault.cfg'
default_log_pattern  = 'tps_tst_{runid}_{timestamp}_{board}_{serial}_{number}.txt'
default_log_name     = 'tps_run_{runid}_{timestamp}_{board}_{serial}.txt'
default_test_pattern = r'test[0-9][0-9]'
default_test_syntax  = r'(test)?(\d\d)'

def run_test(testname, logname):
    """run test testname with output redirected to logname
    """
    try:
        tmpout = sys.stdout
        sys.stdout = open(logname, 'w')
        mod = __import__(testname, globals(), locals(), [])
        mod.main()
    finally:
        sys.stdout.close()
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
        self.read_config(self.config)

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

        try:
            self.board        =  config.get('global', 'board')
            self.serial       =  config.get('global', 'serial')
            self.test_path    =  config.get('global', 'test_path')
            self.log_path     =  config.get('global', 'log_path')
            self.sequence     =  config.get('global', 'sequence')
            self.repeat       =  config.get('global', 'repeat')
            self.randomize    =  config.get('global', 'randomize')
        except NoOptionError:
            pass

    def save(self):
        config = ConfigParser()

        config.add_section('global')
        config.set('global', 'board', self.board)
        config.set('global', 'serial', self.serial)
        config.set('global', 'test_path', self.test_path)
        config.set('global', 'log_path', self.log_path)
        config.set('global', 'sequence', self.sequence)
        config.set('global', 'repeat', self.repeat)
        config.set('global', 'randomize', self.randomize)

        # Writing our configuration file
        configfile = open(self.config, 'wb')
        config.write(configfile)
        configfile.close()

    def validate_and_compute_run(self):
        """validate run paramenters"""

        if not self.board:
            msg = 'invalid board name [{0}]'.format(self.board)
            raise TpsInvalid(msg)
        if not self.serial:
            msg = 'invalid serial number [{0}]'.format(self.serial)
            raise TpsInvalid(msg)

        warnings.simplefilter('error')
        try:
            tmp = os.tempnam(self.test_path)
            open(tmp, 'w')
            os.unlink(tmp)
        except RuntimeWarning:
            pass
        except IOError:
            msg = 'invalid test path [{0}]'.format(self.test_path)
            raise TpsInvalid(msg)

        try:
            tmp = os.tempnam(self.log_path)
            open(tmp, 'w')
            os.unlink(tmp)
        except RuntimeWarning:
            pass
        except:
            msg = 'invalid log path [{0}]'.format(self.log_path)
            raise TpsInvalid(msg)

        if not self.repeat:
            self.repeat = 1
        else:
            try:
                self.repeat = int(self.repeat)
            except ValueError:
                msg = 'invalid repeat factor [{0}]'.format(self.repeat)
                raise TpsInvalid(msg)

        if not self.sequence:
            raise TpsNoBatch('null test sequence')
        run = []
        for testno in self.sequence:
            test_glob = os.path.join(self.test_path, 'test' + testno + '.py')
            files = glob.glob(test_glob)
            if not files:
                print files, test_glob
                raise TpsBadTestNo('no test number [%s], aborting' % testno)
            run.append(files[0])

        if self.randomize:
            random.shuffle(run)

        self.run_ = self.repeat * run

        return self.run_

    def run(self):
        sequence = self.validate_and_compute_run()
        ts          = timestamp()
        runid       = sha(self.board + ':' + self.serial + ':' + ts)
        logfilename = self.log_name.format(board=self.board,
                                serial=self.serial,
                                timestamp=ts,
                                runid=runid)
        logfilename = os.path.join(self.log_path, logfilename)
        log         = file(logfilename, 'wb')

        if self.test_path not in sys.path:
            sys.path.append(self.test_path)

        log.write('test run\n'
            '    board      = {0}\n'
            '    serial     = {1}\n'
            '    timestamp  = {2}\n'
            '    runid      = {3}\n'.format(
                self.board, self.serial, ts, runid))
        failures = []
        for test in sequence:
            try:
                testname = os.path.splitext(os.path.basename(test))[0]
                shortname= re.match('test(\d\d)', testname).group(1)
                logname  = self.log_pattern.format(board=self.board,
                                serial=self.serial,
                                timestamp=timestamp(),
                                runid = runid,
                                number=shortname)
                logname  = os.path.join(self.log_path, logname)
                log.write('------------------------\n')
                log.write('running test {0} = {1}\n'.format(shortname, test))
                print '.',
                run_test(testname, logname)
            except TpsCritical, e:
                print 'test [%s]: critical error, aborting: [%s]' % (shortname, e)
                log.write('    critical error in test {0}, exception [{1}]\n'.format(shortname, e))
                log.write('    cannot continue, aborting test suite')
                failures.append((shortname, e, ))
                break
            except TpsError, e:
                print 'test [%s]: error, continuing: [%s]' % (shortname, e)
                log.write('    error in test {0}, exception [{1}]\n'.format(shortname, e))
                failures.append((shortname, e, ))
            except TpsUser, e:
                print 'test [%s]: user error, user intervention required: [%s]' % (shortname, e)
                log.write('    error in test {0}, exception [{1}]\n'.format(shortname, e))
                failures.append((shortname, e, ))
                while True:
                    if self.yes:
                        log.write('    user intervention: continue (assuming --yes)\n')
                        continue
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
                print 'test [%s]: warning: [%s]' % (shortname, e)
                log.write('    warning in test {0}, exception [{1}]\n'.format(shortname, e))
                failures.append((shortname, e, ))
            else:
                log.write('    OK\n')

        log.write('\n')
        log.write('------------------------\n')
        log.write('Test suite finished.\n')
        if not failures:
            msg = 'All tests OK\n'
        else:
            msg = [ 'FAILED:' ]
            for fail in failures:
                msg.append(fail[0])
            msg = ' '.join(msg)
        print msg
        log.write(msg)
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

def normalize_testname(name):

    if name[:4] == 'test':
        return name[4:]
    return name

def validate_args(args):

    valid_args = [ normalize_testname(arg) for arg in args
            if re.match(default_test_syntax, arg) ]
    invalid_args = [ arg for arg in args
            if not re.match(default_test_syntax, arg) ]
    return valid_args, invalid_args

def main():

    usage = ( '%prog: [options] test ...\n'
            'run %prog with option -h or --help for more help' )
    parser = OptionParser(usage)
    parser.add_option("-c", "--config", dest="config",
                        default=default_config_file,
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
                        default=False,
                        help="run the batch in random order", )
    parser.add_option("-w", "--write-config", action="store_true",
                        help="write configuration data to config file", )
    parser.add_option("-y", "--yes", action="store_true",
                        help="assume all user interventions are affirmative", )

    (options, args) = parser.parse_args()

    # validate arguments and set up Suite object
    if not args:
        parser.print_usage()
        return
    valid, invalid = validate_args(args)
    if invalid:
        print 'invalid test names, aborting:',
        for i in invalid: print i,
        print
        return

    s = Cli(options.config)
    s.__dict__.update(options.__dict__)
    s.sequence = valid
    try:
        s.validate_and_compute_run()
    except TpsInvalid, e:
        print 'bad parameters:', e
        return

    # decide what to do
    if options.write_config:
        s.save()
    elif options.cli:
        s.cmdloop()
    else:
        s.run()

if __name__ == '__main__':
    main()
