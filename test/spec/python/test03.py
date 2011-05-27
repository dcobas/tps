#!/acc/src/dsc/drivers/cohtdrep/siglesia/Python-2.7/python
# It needs Python 2.7 or higher!

import sys
import rr
import time
import os
from ctypes import *
from tpsexcept import *

class CGennumFlash :
    	GENNUM_FLASH = 1;
    	GENNUM_FPGA = 2;
    	FPGA_FLASH = 3; 

	def __init__ (self, bus):
        	self.bus = bus;
	        self.lib = cdll.LoadLibrary("libfpga_loader.so");
        	self.lib.rr_init();
	        self.lib.gpio_init();


def main():

    gennum = rr.Gennum();
    flash = CGennumFlash(gennum);

    start = time.time();
    flash.lib.gpio_bootselect(flash.GENNUM_FLASH);
    version = hex(flash.lib.flash_read_id());
    if (version != "0x202016"):
	raise TpsError('Error: version of the flash is not correct: ' + version);
    
    # Load a new firmware to the Flash memory.
    print "Starting the process to load a FW into Flash memory"
    flash.lib.load_mcs_to_flash("./test_flash.bin");

    time.sleep(1);
    print "Forcing to load FW from Flash memory to FPGA"

    # Force the FPGA to load the FW from the Flash memory

    flash.lib.force_load_fpga_from_flash();
    
    finish = time.time();

    print "Time elapsed: " + str(finish - start) + " seconds" 

    ask = "";
    tmp_stdout = sys.stdout;
    sys.stdout = sys.__stdout__;
    tmp_stdin = sys.stdin;
    sys.stdin = sys.__stdin__;
    while ((ask != "Y") and (ask != "N")) :
    	ask = raw_input("Are the LEDs blinking? [Y/N]")

    sys.stdout = tmp_stdout;
    sys.stdin = tmp_stdin;
    if (ask == "N") :
	raise TpsError("Error loading FW through the Flash memory");


    
        
            
        
                
    
