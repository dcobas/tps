#!   /usr/bin/env   python
#    coding: utf8

import sys
from ply import lex, yacc

tokens = (
    'NUMBER',
    'REPEAT',
    'LPAREN',
    'RPAREN',
    'DASH',
    'TEST',
)

t_NUMBER = r'[0-9]+'
t_REPEAT = r'repeat'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_DASH   = r'-'
t_TEST   = r'test'

t_ignore = ' \t'

def t_error(t):
    print 'Illegal character [%s]' % t.value[0]
    t.lexer.skip(1)

lexer = lex.lex()

def p_battery_sequence(p):
    '''battery : batch
               | batch battery'''
    if len(p) == 2:
        p[0] = [ p[1] ]
    else:
        p[0] = [ p[1] ] + p[2]

def p_batch_single(p):
    'batch : tst'
    p[0] = p[1]

def p_batch_loop(p):
    'batch : REPEAT NUMBER LPAREN battery RPAREN'
    p[0] = [ 'loop', p[2] ] + p[4]

def p_batch_range(p):
    'batch : tst DASH tst'
    p[0] = [ 'range', p[1], p[3] ]

def p_tst(p):
    '''tst : NUMBER
           | TEST NUMBER'''
    p[0] = p[len(p)-1]

def p_error(p):
    print 'syntax error!'

parser = yacc.yacc()

class Sequence(object):
    pass

class Battery(Sequence, list):
    def traverse(self):
        for item in self:
            print item

class Tst(Sequence):
    def traverse(self):
        print self.tag

class Loop(Sequence):
    def traverse(self):
        for i in range(self.number):
            self.sequence.traverse()

class Range(Sequence):
    def traverse(self):
        for i in range(self.fro, self.to+1):
            print i

if __name__ == '__main__':
    result = parser.parse(sys.argv[1])
    print result

