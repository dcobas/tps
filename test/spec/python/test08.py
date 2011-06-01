#!   /usr/bin/env   python
#    coding: utf8

# Copyright CERN, 2011
# Author: Carlos Gil Soriano <cgilsori@cern.ch>
# Licence: GPL v2 or later.
# Website: http://www.ohwr.org

import sys
import os
import rr
import time
import math
import os.path
from tpsexcept import *		# jdgc

""" SPEC test for two clock domains.

This tests checks the 20 MHz system clock and the output of the CDC5662 PLL
"""

# jdgc: path dependencies
test_clk_path = './log/test_clk/'  # jdgc

TEST_TIME_SLOW = 0.25
TOTAL_OF_TESTS = 10

GENNUM_ADDRESS_SPACE = 0x100000
VHDL_WB_SLAVES = 3
VHDL_WB_SLAVE_NUMBER_COUNTER = 0
VHDL_WB_SLAVE_NUMBER_SPI = 1

def wb_addr(vhdl_wb_slave_number):
    return (vhdl_wb_slave_number+1) * (GENNUM_ADDRESS_SPACE >> int(math.ceil(math.log(VHDL_WB_SLAVES + 1,2))))
        	
BASE_WB_2CLK_COUNTER = wb_addr(VHDL_WB_SLAVE_NUMBER_COUNTER)
BASE_WB_SPI = wb_addr(VHDL_WB_SLAVE_NUMBER_SPI)

#def vprint(msg):
#    if (global_mod)


class COpenCoresSPI:

	R_RX = [0x00, 0x04, 0x08, 0x0C]
	R_TX = [0x00, 0x04, 0x08, 0x0C]
	R_CTRL = 0x10
	R_DIV = 0x14
	R_SS = 0x18

	LGH_MASK = (0x7F)
	CTRL_GO = (1<<8)
        CTRL_BSY = (1<<8)
	CTRL_RXNEG = (1<<9)
	CTRL_TXNEG = (1<<10)
	CTRL_LSB = (1<<11)
       	CTRL_IE = (1<<12)
        CTRL_ASS = (1<<13)

        DIV_MASK = (0xFFFF)

        SS_SEL = [0x1, 0x2, 0x4, 0x8, 0x10, 0x20, 0x40]

	conf = 0x0


	def wr_reg(self, addr, val):
		self.bus.iwrite(0, self.base_addr +  addr, 4, val)

	def rd_reg(self, addr):
		return self.bus.iread(0, self.base_addr + addr, 4)


	def __init__(self, bus, base_addr, divider):
		self.bus = bus;
		self.base_addr = base_addr;
		self.wr_reg(self.R_DIV, (divider & self.DIV_MASK));
		# default configuration
		self.conf = self.CTRL_ASS # | self.CTRL_TXNEG

	def wait_busy(self):
		while(self.rd_reg(self.R_CTRL) & self.CTRL_BSY):
			pass

	def config(self, ass, rx_neg, tx_neg, lsb, ie):
		self.conf = 0
		if(ass):
			self.conf |= self.CTRL_ASS
		if(tx_neg):
			self.conf |= self.CTRL_TXNEG
		if(rx_neg):
			self.conf |= self.CTRL_RXNEG
		if(lsb):
			self.conf |= self.CTRL_LSB
		if(ie):
			self.conf |= self.CTRL_IE

	# slave = slave number (0 to 7)
	# data = byte data array to send, in case if read fill with dummy data of the right size

# This transaction has been modified for this test!!
	def transaction(self, slave, data):
		self.wr_reg(self.R_SS, self.SS_SEL[slave])

		txrx = [0x00000000, 0x00000000, 0x00000000, 0x00000000]
                txrx[0] = 0x00FFFFFF & data
                self.wr_reg(self.R_TX[0], txrx[0])

                ctrl_reg = self.CTRL_ASS | self.CTRL_GO | 24

                
		self.wr_reg(self.R_CTRL, 2018)
		self.wr_reg(self.R_CTRL, 2118)
                tmp = (self.rd_reg(self.R_CTRL) >> 8) & 0x00000001
                while(tmp == 1):
                    tmp = (self.rd_reg(self.R_CTRL) >> 8) & 0x00000001
                    #print self.rd_reg(self.R_CTRL)
                    pass

		return txrx


class WB_2CLK_COUNTER:
    CTRL_REG           = 0x0
    SLOW_MAX_VALUE_REG = 0x8
    SLOW_CNT_VALUE_REG = 0xC
    FAST_MAX_VALUE_REG = 0x10
    FAST_CNT_VALUE_REG = 0x14

    BAD_REG = 0x4

    INT_O_FAST = 6
    RUN_FAST   = 5
    RST_FAST   = 4
    INT_O_SLOW = 2
    RUN_SLOW   = 1
    RST_SLOW   = 0

    SLOW_CLK_FREQ = 20        # MHz
    FAST_CLK_FREQ = 125.01       #200      # MHz

    SLOW_CLK_PPM = 100

    # RAKON IVT3200  25 MHz stability specs
    #   Nominal frequency tolerance            2   ppm
    #   Frquency stability over temperature    5   ppm
    #   Frequency slope against temperature    1   ppm/2degC
    #   Static temperature hysteresis          0.6 ppm
    #   Supply voltage stability               0.1 ppm
    #   Load sensitivity                       0.2 ppm
    #   Long term stability                    2   ppm
    # RAKON IVT3200 CONTROL VOLTAGE
    #   Control voltage range                  0.5V to 2.8V
    #   Frequency shift                        6 to 50 ppm
    #      Kv = 2.3/44 ppm/V (+ 6 ppm)

    FAST_RAKON_CLK_KV = 2.3/44

    # CDCM61004 grants 100 ppm after setting up
    FAST_CLK_PPM = 30

    MAX_CYCLES = 0xFFFFFFFF

    def __init__(self, bus, base):
        self.bus = bus;
        self.base = base;
        self.bus.iwrite(0, self.base +  self.CTRL_REG, 4, 0x000000F1)
        self.results = []

# FAIL: Bad first bit
    def set_ctrl_reg(self, value):
        self.bus.iwrite(0, self.base +  self.CTRL_REG, 4, value)

    def rd_ctrl_reg(self):
        return self.bus.iread(0, self.base +  self.CTRL_REG, 4)
 
# OK           
    def set_slow_max_value(self, value):
        self.bus.iwrite(0, self.base +  self.SLOW_MAX_VALUE_REG, 4, value)
# OK
    def rd_slow_max_value(self):
        return self.bus.iread(0, self.base +  self.SLOW_MAX_VALUE_REG, 4)
# OK
    def set_fast_max_value(self, value):
        self.bus.iwrite(0, self.base +  self.FAST_MAX_VALUE_REG, 4, value)
# OK
    def rd_fast_max_value(self):
        return self.bus.iread(0, self.base +  self.FAST_MAX_VALUE_REG, 4)

    def rd_slow_counter(self):
        return self.bus.iread(0, self.base +  self.SLOW_CNT_VALUE_REG, 4)

    def rd_fast_counter(self):
        return self.bus.iread(0, self.base +  self.FAST_CNT_VALUE_REG, 4)

    def translate_to_slow_clk_cycles(self, seconds):
        tmp = seconds*WB_2CLK_COUNTER.SLOW_CLK_FREQ*(10**6)
        if (tmp > WB_2CLK_COUNTER.MAX_CYCLES):
            raise Exception("Bad setting up of the slow clk cycles: Please put a smaller slow clock value")
        return int(tmp)

    def translate_to_fast_clk_cycles(self, seconds):
        tmp = int(math.ceil(seconds*WB_2CLK_COUNTER.FAST_CLK_FREQ*(10**6)))
        if (tmp > WB_2CLK_COUNTER.MAX_CYCLES):
            raise Exception("Bad setting up of the slow clk cycles: Please put a smaller fast clock value\n\tFAST_CLOCK_CYCLES:\t" + "%0.8X"%tmp)
        return int(tmp)

    def rd_bad_reg(self):
        return self.bus.iread(0, self.base +  self.BAD_REG, 4)

    def wr_reg(self, REG_ADDR):
        self.bus.iwrite(0, self.base + REG_ADDR, 4, value)

    def rd_reg(self, REG_ADDR):
        return self.bus.iread(0, self.base + REG_ADDR, 4)

    def run_test(self, test_time_slow):
        global double_counter

        test_time_fast = int(test_time_slow*WB_2CLK_COUNTER.FAST_CLK_FREQ/WB_2CLK_COUNTER.SLOW_CLK_FREQ*1.05)

        double_counter.set_ctrl_reg(0x00000011)
        #print "  CTRL REG\t" + "%.8X"%double_counter.rd_ctrl_reg() + "\tResetting up"

        time.sleep(0.05)
        double_counter.set_ctrl_reg(0x00000000)
        time.sleep(0.05)
        # Then, we fix the max value of the clocks
        # Slow clock is 25MHz
        # Fast clock is 125MHz
        slow_cycles = double_counter.translate_to_slow_clk_cycles(test_time_slow)
        fast_cycles = double_counter.translate_to_fast_clk_cycles(test_time_fast)
        # We put a larger value fo test for fast clock so as to avoid problems
        double_counter.set_slow_max_value(slow_cycles)      # We have to put long values so as to be precises
        double_counter.set_fast_max_value(fast_cycles)      # It has to be bigger than the slow_max_value (in test seconds)
        #print "  Slow max value\t" + "%.8X"%double_counter.rd_slow_max_value()
        #print "  Fast max value\t" + "%.8X"%double_counter.rd_fast_max_value()
        #print "Wishbone clock comparator ready to go\n"
        #print "Test start!"

        double_counter.set_ctrl_reg(0x00000022)

        initial_time = time.localtime().tm_sec;
        time.sleep(test_time_slow * 1.1)
        counter_slow_test_value = double_counter.rd_slow_counter()
        counter_fast_test_value = double_counter.rd_fast_counter()

        #print ""
        print "Slow counter value\t" + "%.8X"%counter_slow_test_value
        print "Fast counter value\t" + "%.8X"%(counter_fast_test_value - 2)      # We substract 2 cycles because of the VHDL CDC
        # counter_fast_test_value += 0x10000		# cause a failure!!!  jdgc
        double_counter.clocks_check(counter_slow_test_value, counter_fast_test_value)
        # Needs some rework

    def clocks_check(self, ticks_slow, ticks_fast):
   
        lower_threshold_n = (1 - self.FAST_CLK_PPM*10**(-6))/(1 + self.SLOW_CLK_PPM*10**(-6))
        upper_threshold_n = (1 + self.FAST_CLK_PPM*10**(-6))/(1 - self.SLOW_CLK_PPM*10**(-6))

        lower_threshold = ticks_slow * self.FAST_CLK_FREQ /self.SLOW_CLK_FREQ * lower_threshold_n
        upper_threshold = ticks_slow * self.FAST_CLK_FREQ /self.SLOW_CLK_FREQ * upper_threshold_n

        print "\tlower_threshold:\t" + "%0.8X"%lower_threshold
        print "\tupper_threshold:\t" + "%0.8X"%upper_threshold
        print "Test checked " + str(len(double_counter.results))
#        print "Threshold\t\t[" + "%0.8X"%lower_threshold + ", " + "%0.8X"%upper_threshold + "]"
        if (ticks_fast < lower_threshold or ticks_fast > upper_threshold):
#            print "Clocks are working badly!"
            self.results.append(False)
        else:
#            print "Clocks are working nicely!" 
            self.results.append(True)

    def write_report (self):
        if not os.path.exists('./log/'):
            print "There"
            os.mkdir('./log')
        if not os.path.exists('./log/test_clk/'):
            os.mkdir('./log/test_clk')
        filename = "test_clk.txt"
        file = open(os.path.join(test_clk_path, filename), 'w')
        tmp_str =  "-------------------------------------------------------------------\n"
        tmp_str += "--                   SPEC V.1.1 Clocks testing                   --\n"
        tmp_str += "-- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - - --\n"
        for i in xrange(len(double_counter.results)):
            tmp_str += "\tTest " + str(i) + "\t"
            if(double_counter.results[i] == False):
                tmp_str += "FAIL\n"
            else:
                tmp_str += "PASS\n"
        file.write(tmp_str)

class AD5662_1:

    PD0 = 16
    PD1 = 17

    OM_NORMAL     = 0
    OM_1K         = 1
    OM_100K       = 2
    OM_TRISTATE   = 3

    V_REF = 3.3

    def __init__(self, spi):
        self.dac_value = 0x0000
        self.op = self.OM_NORMAL
        self.spi = spi

    def set_dac_voltage(self, voltage):
        if (voltage >= self.V_REF):
            "FAIL: please set a valid AD5662_1 voltage"
        value = int(voltage / self.V_REF * 65536)
        self.dac_value = value

    def operation_mode(self, op):
        self.op = op

    def update_output(self):
        data = (self.op << 16) + (self.dac_value)
        self.spi.transaction(0, data)     


def main (default_directory='.'):

    path_fpga_loader = '../firmwares/fpga_loader';
    path_firmware = '../firmwares/test08.bin';
    	
    firmware_loader = os.path.join(default_directory, path_fpga_loader)
    bitstream = os.path.join(default_directory, path_firmware)
    os.system( firmware_loader + ' ' + bitstream)

    time.sleep(2);

    global double_counter

    gennum = rr.Gennum();
    double_counter = WB_2CLK_COUNTER(gennum, BASE_WB_2CLK_COUNTER)

    print "-------------------------------------------------------------------"
    print "--                   SPEC V.1.1 Clocks testing                   --"
    print "-- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - - --"
    print " CERN BE-CO-HT                     Visit us!   www.ohwr.org        "
    print "                                         "
    print " This test is intended for testing the  system clock (20 MHz) and  "
    print " the PLL clock (CDCM61004)"
    print " The following circuits are tested as well:"
    print "   - IC3 AD5662BRMZ-1"
    print "   - OSC1 IVT3205CR 25.0MHz"
    print "-- - - - - - - - - - -  - - - - - --"
    print "  TEST PARAMS"
    print "-- - - - - - - - - - -  - - - - - --"
    print "Wishbone counter address\t" + "%.8X"%BASE_WB_2CLK_COUNTER
    print "Wishbone SPI address\t\t" + "%.8X"%BASE_WB_SPI
    print "Number of tests\t\t\t" + str(TOTAL_OF_TESTS)
    print "Elapsed time per test\t\t" + str(TEST_TIME_SLOW)

    spi_device = COpenCoresSPI(gennum, BASE_WB_SPI, 0x0004) # Configuring with a 4 means a SCLK frequency of 5 MHz
    dac = AD5662_1(spi_device)
    dac.operation_mode(dac.OM_NORMAL)
    dac.set_dac_voltage(1.65)
    dac.update_output()

    print "* AD5662_1 set up for PLL reference clock\tOK"

    for i in range (0, TOTAL_OF_TESTS):
        double_counter.run_test(TEST_TIME_SLOW)
    for i in range (0, len(double_counter.results)):
        if (double_counter.results[i] == False):
            print "Test " + str(i) +":\tFAIL"
            raise TpsCritical("Mismatch between expected fast cycles and expected ones")
        else:
            print "Test " + str(i) +":\tPASS"

    double_counter.write_report()

if __name__ == '__main__':
	main()
