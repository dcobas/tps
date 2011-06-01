#!   /usr/bin/env   python
#    coding: utf8

# Copyright CERN, 2011
# Author: Samuel Iglesias Gonsalvez <siglesia@cern.ch>
# Licence: GPL v2 or later.
# Website: http://www.ohwr.org

import sys
import rr
import random
import time
import spi
import i2c
import gn4124
import os

"""
test07: checks data and address lines of DDR memory.
"""

GN4124_CSR = 0x0

	
def main (default_directory='.'):

    path_fpga_loader = '../firmwares/fpga_loader';
    path_firmware = '../firmwares/test07.bin';
    	
    firmware_loader = os.path.join(default_directory, path_fpga_loader)
    bitstream = os.path.join(default_directory, path_firmware)
    os.system( firmware_loader + ' ' + bitstream)

    time.sleep(2);

    # Objects declaration
    spec = rr.Gennum() # bind to the SPEC board
    gennum = gn4124.CGN4124(spec, GN4124_CSR)

    print '\n### Configuration ###'

    # Set local bus frequency
    gennum.set_local_bus_freq(160)
    print("GN4124 local bus frequency: %d") % gennum.get_local_bus_freq()

    print '\nStart test'

    # Get host memory pages physical address
    pages = gennum.get_physical_addr()

    num_addr_lines = 64;
    num_data_lines = 16;

    if (len(pages) < (num_addr_lines + 2)) :
	raise Exception("Not enough pages");

    # Clear memory pages
    gennum.set_memory_page(0, 0x0)
    gennum.set_memory_page(1, 0xBABEFACE)
    gennum.set_memory_page(2, 0x0)
    dma_length = 0x400 # DMA length in bytes

    t1 = time.time();

    print "Test Address lines"
    error = 0;
    for i in range(num_addr_lines) :
	if (i==0) :
		continue;

	for j in range(num_addr_lines/2) :
            t3 = time.time();
            if (i != 2*j) :
                gennum.add_dma_item((1 << 2*j), pages[2], dma_length, 1, 1)
                gennum.add_dma_item((1 << 2*j), pages[3+2*j], dma_length, 0, 0)
            	gennum.start_dma()
            	gennum.wait_irq()


            if ((2*j+1) != i) :
                gennum.add_dma_item((1 << (2*j+1)), pages[2], dma_length, 1, 1)
                gennum.add_dma_item((1 << (2*j+1)), pages[3+(2*j+1)], dma_length, 0, 0)
            	gennum.start_dma()
            	gennum.wait_irq()

        gennum.add_dma_item((1 << i), pages[1], dma_length, 1, 1)
        gennum.add_dma_item((1 << i), pages[3+i], dma_length, 0, 0)
        gennum.start_dma()
        gennum.wait_irq()
                                        

	page_data = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];
        for j in range(num_addr_lines):
	    page_data[j] = gennum.get_memory_page(3+j)
	    if (j == i) :
		if (page_data[j][0] != 0xBABEFACE):
                    print("\n### Compare error @ addr line:0x%.8X wr:0x%.8X rd:0x%.8X") % (j,0xBABEFACE, page_data[j][0])
                    error = 1;
            else :
                if(page_data[j][0] != 0x0):
                    print("\n### Compare error @ addr line:0x%.8X wr:0x%.8X rd:0x%.8X") % (j,0x0, page_data[j][0])
                    error = 1;

    if (error) :
	print "RESULT: [FAILED]"
    else :
	print "RESULT: [OK]"

    print "Test Data lines"
    error = 0;
    for i in range(num_data_lines) :
	
    	gennum.set_memory_page(1, (1<<i))
        gennum.add_dma_item(0, pages[1], dma_length, 1, 1)
        gennum.add_dma_item(0, pages[2], dma_length, 0, 0)
        gennum.start_dma()
        gennum.wait_irq()
	page_data = gennum.get_memory_page(2);

	if (page_data[0] != (1 << i)) :
	    print("### Compare error @ data line:0x%.8X wr:0x%.8X rd:0x%.8X") % (i,(1 << i), page_data[0])
	    error = 1;

    if (error) :
	print "RESULT: [FAILED]"
    else :
	print "RESULT: [OK]"

    t2 = time.time();
    print 'End of test'
    print 'Time DDR test: ' + str(t2-t1) + ' seconds'


if __name__ == '__main__' :
	main();
