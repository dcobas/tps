#!/acc/src/dsc/drivers/cohtdrep/siglesia/Python-2.7/python
# It needs Python 2.7 or higher!

import ctypes
from multiprocessing import Process

import sys
import rr
import time
import os
from tpsexcept import *



TX_SIZE = 32;          # Number of Bytes to TX
RX_SIZE = TX_SIZE;     # Number of Bytes to RX

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
			raise TpsError('No ACK upon address (device 0x%x not connected?)' % (addr >> 1))

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

class SWITCH_ADN4600:
        # Only basic mode is implemented
        RST = 0x0;
        XPT_CFG = 0x40;
        XPT_UPDATE = 0x41;
        XPT_STAT_0 = 0x50;   XPT_STAT_1 = 0x51;    XPT_STAT_2 = 0x52;   XPT_STAT_3= 0x53
        XPT_STAT_4 = 0x54;   XPT_STAT_5 = 0x55;    XPT_STAT_6 = 0x56;   XPT_STAT_7= 0x57
	RX0_CONF = 0x80;     RX1_CONF = 0x88;      RX2_CONF = 0x90;     RX3_CONF = 0x98;
	RX4_CONF = 0xA0;     RX5_CONF = 0xA8;      RX6_CONF = 0xB0;     RX7_CONF = 0xB8;
	TX0_CONF = 0xC0;     TX1_CONF = 0xC8;      TX2_CONF = 0xD0;     TX3_CONF = 0xD8;
	TX4_CONF = 0xE0;     TX5_CONF = 0xE8;      TX6_CONF = 0xF0;     TX7_CONF = 0xF8;

        def __init__(self, i2c, addr):
            self.i2c = i2c;
            self.addr = addr;

        def wr_reg8(self, bank, value):
            self.i2c.start(self.addr, True); # write cycle
            self.i2c.write(bank, False);
            self.i2c.write(value, True);	

	def rd_reg8(self, bank):
            self.i2c.start(self.addr, True);
            self.i2c.write(bank, False);
            self.i2c.start(self.addr, False);
            return self.i2c.read(True);

        def passby_input_output(self, channel_input, channel_output):
            # If the channel_output is -1, it means broadcast to all output channels!
            if (channel_output == -1):
                data = (channel_input << 4) | (1 << 3);
            else :
                data = (channel_input << 4) | (channel_output);
            
            self.wr_reg8(self.XPT_CFG, data);
            self.wr_reg8(self.XPT_UPDATE, 0x1);

	def rx_logic(self, channel, negate) :
		self.wr_reg8(0x80 + 0x8*channel, (negate << 6) | (1 << 5) | (1 << 4))

	def enable_tx(self, channel) :
		self.wr_reg8(0xC0 + 0x8*channel, (1 << 5))


class CMinic:
	OFFSET_EP = 0x4000
	OFFSET_PMEM = 0x8000
	OFFSET_MINIC = 0x0
	
	EP_REG_ECR = 0x0
	EP_REG_MACL = 0x14
	EP_REG_MACH = 0x10
	EP_REG_MDIO_CR = 0x20
	EP_REG_MDIO_SR = 0x24
	EP_REG_IDCODE = 0x28
	EP_REG_RFCR = 0x8
	EP_REG_TSCR = 0x4
	
	EP_MDIO_CR_RW = 0x80000000
	EP_MDIO_SR_READY = 0x80000000
	
	EP_ECR_TX_EN = 0x40
	EP_ECR_RX_EN = 0x80
	
	MINIC_REG_MCR = 0x0
	MCR_TX_START = 0x1
	MCR_TX_IDLE = 0x2
	MCR_TX_ERROR = 0x4
	MCR_RX_READY = 0x100
	MCR_RX_FULL = 0x200
	MCR_RX_EN = 0x400
	
	MINIC_REG_RX_ADDR = 0x8
	MINIC_REG_RX_AVAIL = 0xc
	MINIC_REG_TX_ADDR = 0x4

	MINIC_REG_EIC_IDR = 0x20
	MINIC_REG_EIC_IER = 0x24
	MINIC_REG_EIC_IMR = 0x28
	MINIC_REG_EIC_ISR = 0x2c
	MINIC_EIC_ISR_RX = 1 << 1
	
	TX_DESC_VALID = 1 << 31
	TX_DESC_HAS_OWN_MAC = 1 << 28
	
	
	
	def __init__(self, bus, base, num):
	    self.base =base;
	    self.bus = bus;
	    self.num = num;
	    self.init_ep();
	    
	def ep_readl(self, addr):
	    return self.bus.iread(0, self.base + self.OFFSET_EP + addr, 4)

	def ep_writel(self, addr, val):
	    self.bus.iwrite(0, self.base + self.OFFSET_EP + addr, 4, val)

	def minic_readl(self, addr):
	    return self.bus.iread(0, self.base + self.OFFSET_MINIC + addr, 4)

	def minic_writel(self, addr, val):
	    self.bus.iwrite(0, self.base + self.OFFSET_MINIC + addr, 4, val)

	def pmem_writel(self, addr, val):
	    self.bus.iwrite(0, self.base + self.OFFSET_PMEM + addr, 4, val)

	def pmem_readl(self, addr):
	    return self.bus.iread(0, self.base + self.OFFSET_PMEM + addr, 4);
	    
	def pcs_readl(self, addr):
            val = 0
	    self.ep_writel(self.EP_REG_MDIO_CR, addr << 16);
	    while (val & self.EP_MDIO_SR_READY) == 0:
		val = self.ep_readl(self.EP_REG_MDIO_SR)
	    return (val & 0xffff)
	    
	def start_rx(self):
	    self.ep_writel(self.EP_REG_ECR, 0)
	    self.ep_writel(self.EP_REG_MACL, 0xfc969b0e)
	    self.ep_writel(self.EP_REG_MACH, 0x0050 + self.num)
	    self.ep_writel(self.EP_REG_ECR, self.EP_ECR_TX_EN | self.EP_ECR_RX_EN)
	    self.ep_writel(self.EP_REG_RFCR, 3 << 4)
	    self.ep_writel(self.EP_REG_TSCR, 1 + 2)
	    self.minic_writel(self.MINIC_REG_MCR, 0)
	    self.minic_writel(self.MINIC_REG_RX_ADDR, 0)
	    self.minic_writel(self.MINIC_REG_RX_AVAIL, 4000)
	    self.minic_writel(self.MINIC_REG_EIC_IER, self.MINIC_EIC_ISR_RX)
	    self.minic_writel(self.MINIC_REG_MCR, self.MCR_RX_EN)

	def init_ep(self):
	    self.ep_writel(self.EP_REG_ECR, 0)
	    self.ep_writel(self.EP_REG_MACL, 0xfc969b0e)
	    self.ep_writel(self.EP_REG_MACH, 0x0050 + self.num)
	    self.ep_writel(self.EP_REG_RFCR, 3 << 4)
	    self.ep_writel(self.EP_REG_TSCR, 1 + 2)
	    self.ep_writel(self.EP_REG_ECR, self.EP_ECR_TX_EN | self.EP_ECR_RX_EN)

	def test_tx(self):
	    self.pmem_writel(0, (1<<31) | 64);
	    self.pmem_writel(4, 0xffffffff)
	    self.pmem_writel(8, 0xffffffff)
	    self.pmem_writel(12, 0xffffffff)
	    self.pmem_writel(16, 0xffffffff)
	    self.minic_writel(self.MINIC_REG_TX_ADDR, 0);
	    self.minic_writel(self.MINIC_REG_MCR, self.MCR_TX_START);
	
	def link_up(self):
	    return self.pcs_readl(1) & 4

  	def send(self) :
        	# Setup TX
        	self.minic_writel(self.MINIC_REG_TX_ADDR, 0);

        	# Enable TX and wait for the end of the operation
        	self.minic_writel(self.MINIC_REG_MCR, self.MCR_TX_START);

		mask = 1 << 1;
		while((self.minic_readl(self.MINIC_REG_MCR) & mask) == 0) :
			print "."

		mask = 1 << 2;
		if(self.minic_readl(self.MINIC_REG_MCR) & mask) :
			raise TpsError('MINIC: TX error');

    	def receive(self, size) :
        	# Setup RX
		self.start_rx();
		self.poll_rx();
		return self.read_buffer(size)

	def read_status(self) :
		return self.minic_readl(self.MINIC_REG_MCR);

	def poll_rx(self) :
		while(True) :
			isr = self.minic_readl(self.MINIC_REG_EIC_ISR);	
			if (isr & self.MINIC_EIC_ISR_RX) :
				# Clear interrupt!
				self.minic_writel(self.MINIC_REG_EIC_ISR, self.MINIC_EIC_ISR_RX)
				break


	def create_header_tx(self, size) :
		nwords = ((size + 1) >> 1) - 1;
		header = self.TX_DESC_VALID | nwords #| self.TX_DESC_HAS_OWN_MAC | nwords;
		return header;

	def write_buffer(self, value, size) :
		mask = 0xffffffff;
		header = self.create_header_tx(size)
		self.pmem_writel(0, header);
		for i in range(1, size) :
		    tmp = (value >> (i - 1)*32) & mask;
		    self.pmem_writel(i*4, tmp);

		self.pmem_writel(size*4, 0);

	def read_buffer(self, size):
		value = 0;
		mask = 0xffffffff;
		for i in range(0,size) :
		    value = value | ((self.pmem_readl(i*4) & mask) << i*4);

		return value;

def rx_thread(minic, size):

    print "Waiting for RX the data..."
    for i in range(1,10):
        print "Received ["+ str(i) +"]: "+ hex(minic.receive(size))

        

def main():

    bitstream_name = 'test_sata.bin'
    os.system('/user/siglesia/vhdl/gennum/fpga_loader/gnurabbit/user/fpga_loader_test /user/siglesia/vhdl/gennum/fpga_loader/gnurabbit/user/'+bitstream_name);
    time.sleep(1);
    
    gennum = rr.Gennum();

    i2c = COpenCoresI2C(gennum, 0x40000, 99);
    adn4600 = SWITCH_ADN4600(i2c, 0x48);

    adn4600.enable_tx(0)
    adn4600.enable_tx(1)
    adn4600.enable_tx(2)
    adn4600.enable_tx(3)
    adn4600.enable_tx(4) # channel 6
    adn4600.enable_tx(5) # channel 7
    adn4600.enable_tx(6) # channel 5
    adn4600.enable_tx(7) # channel 4

    print "adn4600 tx 1-0: " + hex(adn4600.rd_reg8(0xC8)) + " " + hex(adn4600.rd_reg8(0xC0))
    print "adn4600 tx 3-2: " + hex(adn4600.rd_reg8(0xD8)) + " " + hex(adn4600.rd_reg8(0xD0))
    print "adn4600 tx 5-4: " + hex(adn4600.rd_reg8(0xF0)) + " " + hex(adn4600.rd_reg8(0xF8))
    print "adn4600 tx 7-6: " + hex(adn4600.rd_reg8(0xE0)) + " " + hex(adn4600.rd_reg8(0xE8))


    adn4600.rx_logic(0, 1)
    adn4600.rx_logic(1, 1)
    adn4600.rx_logic(2, 1)
    adn4600.rx_logic(3, 1)
    adn4600.rx_logic(4, 1)
    adn4600.rx_logic(5, 1)
    adn4600.rx_logic(6, 1)
    adn4600.rx_logic(7, 1)

    print "adn4600 rx logic 1-0: " + hex(adn4600.rd_reg8(0x88)) + " " + hex(adn4600.rd_reg8(0x80))
    print "adn4600 rx logic 3-2: " + hex(adn4600.rd_reg8(0x98)) + " " + hex(adn4600.rd_reg8(0x90))
    print "adn4600 rx logic 5-4: " + hex(adn4600.rd_reg8(0xA8)) + " " + hex(adn4600.rd_reg8(0xA0))
    print "adn4600 rx logic 7-6: " + hex(adn4600.rd_reg8(0xB8)) + " " + hex(adn4600.rd_reg8(0xB0))

    time.sleep(1)
    adn4600.passby_input_output(0x4, 0x1);
    adn4600.passby_input_output(0x6, 0x6);
    print "adn4600 1-0: " + hex(adn4600.rd_reg8(0x51)) + " " + hex(adn4600.rd_reg8(0x50))
    print "adn4600 3-2: " + hex(adn4600.rd_reg8(0x53)) + " " + hex(adn4600.rd_reg8(0x52))
    print "adn4600 5-4: " + hex(adn4600.rd_reg8(0x55)) + " " + hex(adn4600.rd_reg8(0x54))
    print "adn4600 7-6: " + hex(adn4600.rd_reg8(0x57)) + " " + hex(adn4600.rd_reg8(0x56))

    time.sleep(1)

    minic_sata = CMinic(gennum, 0x20000, 0);
    minic_sata.init_ep()

    minic_dp0 = CMinic(gennum, 0x60000, 1);
    minic_dp0.init_ep()

    minic_sata1 = CMinic(gennum, 0xA0000, 2);
    minic_sata1.init_ep()

    minic_sfp = CMinic(gennum, 0x80000, 3);
    minic_sfp.init_ep()

    size = 129;


    p = Process(target=rx_thread, args=(minic_dp0, size));
    p.start();
    # Send the data
    time.sleep(1);

    print "SATA 0 tx: "
    for i in range(1,10):
	minic_sata.test_tx()
	time.sleep(1);
	print "Transmitted [" + str(i) + "]"

    print "Done"

    if (p.is_alive()) :
	p.terminate();
	raise TpsUser("Test SATA -> DP0: Error in DP0, RX")
 
    time.sleep(2);

    p = Process(target=rx_thread, args=(minic_sata, size));
    p.start();
    # Send the data
    time.sleep(1);

    print "DP0 tx: "
    for i in range(1,10):
	minic_dp0.test_tx()
	time.sleep(1);
	print "Transmitted [" + str(i) + "]"

    print "Done"

    if (p.is_alive()) :
	p.terminate();
	raise TpsUser ("Test DP0 -> SATA 0: Error in SATA 0, RX")
 
    time.sleep(2)    

    ask = "";
    print "\n*************************************************************"
    while ((ask != "Y") and (ask != "N")) :
    	ask = raw_input("Please, now connect a SATA cable between FMC tester and SATA 1 connector. Is it done? [Y/N]")

    if (ask == "N") :
	raise TpsWarning("Test DP0-SATA 1 cancelled");


    p = Process(target=rx_thread, args=(minic_dp0, size));
    p.start();
    # Send the data
    time.sleep(1);

    print "SATA 1 tx: "
    for i in range(1,10):
	minic_sata1.test_tx()
	time.sleep(1);
	print "Transmitted [" + str(i) + "]"

    print "Done"

    if (p.is_alive()) :
	p.terminate();
	raise TpsError ("Test SATA1 -> DP0: Error in DP0, RX")
 
    time.sleep(2);

    p = Process(target=rx_thread, args=(minic_sata1, size));
    p.start();
    # Send the data
    time.sleep(1);

    print "DP0 tx: "
    for i in range(1,10):
        #minic_sata.send();
	minic_dp0.test_tx()
	time.sleep(1);
	print "Transmitted [" + str(i) + "]"

    print "Done"

    if (p.is_alive()) :
	p.terminate();
	raise TpsError ("Test DP0 -> SATA1: Error in SATA 1, RX")
 
