#!/bin/sh

rm -fr /tmp/tps*

serial=$1
if [ x$1 == x"" ]; then
	echo -n "Please, input SERIAL number: "
        read serial
fi

time ./tps.py -b SPEC -s $serial -t./test/spec/python -l /tmp 00 01 02 03 05 06 07 08

