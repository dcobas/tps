#!   /usr/bin/env   python
#    coding: utf8

# Copyright CERN, 2011
# Author: Samuel Iglesias Gonsalvez <siglesia@cern.ch>
# Licence: GPL v2 or later.
# Website: http://www.ohwr.org

import sys
import rr
import time
import os
from tpsexcept import *

"""
test00: checks voltage of the power pins in FMC connector.
"""

BASE_GPIO = 0x40000
BASE_MINIC = 0xc0000
GPIO_CODR = 0x0
GPIO_SODR = 0x4
GPIO_PSR = 0xc
        	
class COpenCoresI2C:
	R_PREL = 0x0
	R_PREH = 0x4
	R_CTR = 0x8
	R_TXR = 0xC
	R_RXR = 0xC
	R_CR = 0x10
	R_SR = 0x10
	
	CTR_EN = (1<<7)
	
	CR_STA = (1<<7)
	CR_STO = (1<<6)
	CR_WR = (1<<4)
	CR_RD = (1<<5)
	CR_NACK = (1<<3)
	
	SR_RXACK = (1<<7)
	SR_TIP = (1<<1)
	
	
	def wr_reg(self, addr, val):
		self.bus.iwrite(0, self.base +  addr, 4, val)

	def rd_reg(self,addr):
		return self.bus.iread(0, self.base + addr, 4)
	
	def __init__(self, bus, base, prescaler):
		self.bus = bus;
		self.base =base;
		self.wr_reg(self.R_CTR, 0);
		self.wr_reg(self.R_PREL, (prescaler & 0xff))
		self.wr_reg(self.R_PREH, (prescaler >> 8))
		self.wr_reg(self.R_CTR, self.CTR_EN);
	
	def wait_busy(self):
		while(self.rd_reg(self.R_SR) & self.SR_TIP):
			pass
	
	def start(self, addr, write_mode):
		addr = addr << 1
		if(write_mode == False):
			addr = addr | 1;
		self.wr_reg(self.R_TXR, addr);
		self.wr_reg(self.R_CR, self.CR_STA | self.CR_WR);
		self.wait_busy()
		
		if(self.rd_reg(self.R_SR) & self.SR_RXACK):
			raise Exception('No ACK upon address (device 0x%x not connected?)' % addr)

	def write(self, data, last):
		self.wr_reg(self.R_TXR, data);
		cmd = self.CR_WR;
		if(last):
			cmd = cmd | self.CR_STO;
		self.wr_reg(self.R_CR, cmd);
		self.wait_busy();
		if(self.rd_reg(self.R_SR) & self.SR_RXACK):
			raise Exception('No ACK upon write')

	def read(self, last):
		cmd = self.CR_RD;
		if(last):
			cmd = cmd | self.CR_STO | self.CR_NACK;
		self.wr_reg(self.R_CR, cmd);
		self.wait_busy();
		
		return self.rd_reg(self.R_RXR);

class ADC_AD7997:
	CONVER_R = 0x00;
	CONFIG_R = 0x02;
	CH8 = (1 << 11);
	CH7 = (1 << 10);
	CH6 = (1 << 9);
	CH5 = (1 << 8);
	CH4 = (1 << 7);
	CH3 = (1 << 6);
	CH2 = (1 << 5);
	CH1 = (1 << 4);

	def __init__(self, i2c, addr):
		self.i2c = i2c;
		self.addr = addr;

	def wr_reg16(self, addr, value):
		self.i2c.start(self.addr, True);
		self.i2c.write(addr, False);
		tmp = (value >> 8) & 0xFF;
		self.i2c.write(value, False);
		tmp = value & 0xFF;
		self.i2c.write(value, True)

	def wr_reg8(self, addr, value):
		self.i2c.start(self.addr, True); # write cycle
		self.i2c.write(addr, False);
		self.i2c.write(value, True);	

	def rd_reg16(self, addr):
		self.i2c.start(self.addr, True);
		self.i2c.write(addr, False);
		self.i2c.start(self.addr, False);
		tmp_MSB = self.i2c.read(False);
		tmp_LSB = self.i2c.read(True);
		value = (tmp_MSB << 8) | tmp_LSB;
		return value;

	def rd_reg8(self, addr):
		self.i2c.start(self.addr, True);
		self.i2c.write(addr, False);
		self.i2c.start(self.addr, False);
		return self.i2c.read(True);	

def adc_value(value) :
	return str(2.495 * (0x3FF & (value >> 2)) / 1024); # 10 bits
	
def main (default_directory='.'):

	path_fpga_loader = '../firmwares/fpga_loader';
	path_firmware = '../firmwares/test00.bin';
    	
	firmware_loader = os.path.join(default_directory, path_fpga_loader)
    	bitstream = os.path.join(default_directory, path_firmware)
    	os.system( firmware_loader + ' ' + bitstream)

    	time.sleep(2);
    
	gennum = rr.Gennum();

	i2c = COpenCoresI2C(gennum, 0x40000, 99); # Prescaler value calculated using 50 MHz clock

	# The address of the AD7997 is 0x23, pin 15 connected to GND.
	adc = ADC_AD7997(i2c, 0x23);

	value8 = adc_value(adc.rd_reg16(0xF0));
	value7 = adc_value(adc.rd_reg16(0xE0));
	value6 = adc_value(adc.rd_reg16(0xD0));
	value5 = adc_value(adc.rd_reg16(0xC0));
	value4 = adc_value(adc.rd_reg16(0xB0));
	value3 = adc_value(adc.rd_reg16(0xA0));
	value2 = adc_value(adc.rd_reg16(0x90));
	value1 = adc_value(adc.rd_reg16(0x80));

	# Check the values of the ADC.
	if(float(value8) < 1.61) or (float(value8) > 1.73) :
		raise TpsError ("Error in VS_VADJ, value x=" + value8 + ". x > 1.73 V or x < 1.61 V")
	print "VS_VADJ = " + value8

	if(float(value7) < 1.90) or (float(value7) > 2.11):
		raise TpsError ("Error in VS_P12V_x, value x=" + value7 + ". x< 1.90 V or x > 2.11 V")
	print "VS_P12V_x = " + value7

	if(float(value6) < 1.66) or (float(value6) > 1.80):
		raise TpsError ("Error in VS_P3V3_x, value x=" + value6 + ". x < 1.66 V or x > 1.80 V")
	print "VS_P3V3_x = " + value6

"""
	if(float(value5) < 2.52) :
		print "Error in P5V_BI, value " + value5 + " < 2.52 V"
	print "P5V_BI = " + value5

	if(float(value4) > 2.0) :
		print "Error in M2V_BI, value " + value4 + " > 2.0 V"
	print "M2V_BI = " + value4

	if(float(value3) > 2.28) :
		print "Error in M5V2_BI, value " + value3 + " > 2.28 V"
	print "M5V2_BI = " + value3

	if(float(value2) > 2.4) :
		print "Error in M12V_BI, value " + value2 + " > 2.4 V"
	print "M12V_BI = " + value2

	if(float(value1) < 2.0) :
		print "Error in P12V_BI, value " + value1 + " < 2.0 V"
	print "P12V_BI = " + value1
"""

if __name__ == '__main__' :
	main();

