#!/bin/sh

rm /tmp/tps*

time ./tps.py -b SPEC -s $1 -t./test/spec/python -l /tmp 00 01 02 03 05 06 07 08
