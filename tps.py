#!   /usr/bin/env   python
#    coding: utf8

import sys
import cmd
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

    def run(self):
        pass

    def write_cfg(self):
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

def timestamp():
    """timestamp for now
    """
    return datetime.datetime.now().strftime('%Y%m%d.%H%M%S')

def sha(blob, len=7):
    """create a sha-160 hash of a binary object

    len is the number of hex digits to take from the hex digest,
    defaulting to 7 just as in git
    """

    hash = sha160(blob)
    ret = hash.hexdigest()
    if len:
        return ret[:len]
    
if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("-c", "--config", dest="config",
                        default=default_config_file,
                        help="config file name", metavar="FILE")

    (options, args) = parser.parse_args()

    s = Suite(options.config)
    s.write_cfg()
