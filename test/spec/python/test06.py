#!/acc/src/dsc/drivers/cohtdrep/siglesia/Python-2.7/python
# It needs Python 2.7 or higher!

import sys
import rr
import time
import os
from tpsexcept import *

"""
test06: checks Silabs SI570 oscillator.
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
			raise TpsError('No ACK upon address (device 0x%x not connected?)' % addr)

	def write(self, data, last):
		self.wr_reg(self.R_TXR, data);
		cmd = self.CR_WR;
		if(last):
			cmd = cmd | self.CR_STO;
		self.wr_reg(self.R_CR, cmd);
		self.wait_busy();
		if(self.rd_reg(self.R_SR) & self.SR_RXACK):
			raise TpsError('No ACK upon write')

	def read(self, last):
		cmd = self.CR_RD;
		if(last):
			cmd = cmd | self.CR_STO | self.CR_NACK;
		self.wr_reg(self.R_CR, cmd);
		self.wait_busy();
		
		return self.rd_reg(self.R_RXR);

class CSI570 :
	
	HS_N1_DIV = 0x7;
	REF_FREQ_37_32 = 0x8;
	REF_FREQ_31_24 = 0x9;
	REF_FREQ_23_16 = 0xA;
	REF_FREQ_15_8 = 0xB;
	REF_FREQ_7_0 = 0xC;
	RST_MEM_CTRL = 0x87;
	FREEZE_DCO = 0x89;
	

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
	
	def setup_oscillator(self, hs_div, n1_div, rfreq) :
		val = ((hs_div & 0x7) << 5) | (n1_div >> 2)
		self.wr_reg8(self.HS_N1_DIV, val);

		val = ((n1_div & 0x3) << 6) | (rfreq >> 32);
		self.wr_reg8(self.REF_FREQ_37_32, val);

		val = (rfreq >> 24) & 0xFF;
		self.wr_reg8(self.REF_FREQ_31_24, val);

		val = (rfreq >> 16) & 0xFF;
		self.wr_reg8(self.REF_FREQ_23_16, val);

		val = (rfreq >> 8) & 0xFF;
		self.wr_reg8(self.REF_FREQ_15_8, val);
		
		val = rfreq & 0xFF;
		self.wr_reg8(self.REF_FREQ_7_0, val);

	def reset(self) :
		val = (1 << 7);
		self.wr_reg8(self.RST_MEM_CTRL, val);

	
def main (default_directory='.'):

    path_fpga_loader = '../firmwares/fpga_loader';
    path_firmware = '../firmwares/test06.bin';
    	
    firmware_loader = os.path.join(default_directory, path_fpga_loader)
    bitstream = os.path.join(default_directory, path_firmware)
    os.system( firmware_loader + ' ' + bitstream)

    time.sleep(2);

    gennum = rr.Gennum();

    i2c = COpenCoresI2C(gennum, 0x40000, 99); # Prescaler value calculated using 50 MHz clock

# The address of the SI570 is fixed in the part number
    si570 = CSI570(i2c, 0x55);

    si570.setup_oscillator(1, 0, 0);

    time.sleep(1)

    if (gennum.iread(0,0x80000,4)) :
	print "SI570 CLK present: OK"
    else :
	raise TpsError("SIS570 CLK present: FAILED")


if __name__ == '__main__' :
	main();
