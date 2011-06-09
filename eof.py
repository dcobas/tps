#!   /user/dcobas/2.7.1/bin/python
#    coding: utf8

import sys

if __name__ == '__main__':
    input = sys.stdin
    x = raw_input('Dime algo')
    print 'x = [{0}]'.format(x)
    try:
        sys.stdin = file('/dev/null')
        x = raw_input('Dime algo')
        print 'x = [{0}]'.format(x)
    except EOFError:
        print 'found EOF when reading from redirected stdin'
    sys.stdin = input
    x = raw_input('Dime algo')
    print 'x = [{0}]'.format(x)


