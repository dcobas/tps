#!   /usr/bin/env   python
#    coding: utf8


import sys
import rr
import time
import os
import errno

from tpsexcept import *		# jdgc

"""
test01: checks the low speed pins of FMC connector (low count connector).
"""

tests_path = '.'
default_log_path = '.'

# Mapping for seven slaves!
BASE_I2C_B = 0x20000
BASE_GPIO0 = 0x40000
BASE_GPIO1 = 0x60000
BASE_GPIO2 = 0x80000

FMC_SPEC_ROLL_0_TEST_ID_CC_gpio_to_i2c_16bits = 0x00
FMC_SPEC_ROLL_1_TEST_ID_CC_gpio_to_i2c_16bits = 0x01
FMC_SPEC_ROLL_0_TEST_ID_CC_i2c_to_gpio_16bits = 0x02
FMC_SPEC_ROLL_1_TEST_ID_CC_i2c_to_gpio_16bits = 0x03

FMC_SPEC_ROLL_0_TEST_ID_CC_gpio_to_i2c_32bits = 0x04
FMC_SPEC_ROLL_1_TEST_ID_CC_gpio_to_i2c_32bits = 0x05
FMC_SPEC_ROLL_0_TEST_ID_CC_i2c_to_gpio_32bits = 0x06
FMC_SPEC_ROLL_1_TEST_ID_CC_i2c_to_gpio_32bits = 0x07

FMC_SPEC_ROLL_0_TEST_ID_CC_gpio_to_i2c_64bits = 0x08
FMC_SPEC_ROLL_1_TEST_ID_CC_gpio_to_i2c_64bits = 0x09
FMC_SPEC_ROLL_0_TEST_ID_CC_i2c_to_gpio_64bits = 0x0A
FMC_SPEC_ROLL_1_TEST_ID_CC_i2c_to_gpio_64bits = 0x0B

FMC_SPEC_ROLL_0_TEST_ID_CC_gpio_to_i2c_96bits = 0x0C
FMC_SPEC_ROLL_1_TEST_ID_CC_gpio_to_i2c_96bits = 0x0D
FMC_SPEC_ROLL_0_TEST_ID_CC_i2c_to_gpio_96bits = 0x0E
FMC_SPEC_ROLL_1_TEST_ID_CC_i2c_to_gpio_96bits = 0x0F

testStatus = {}

gpio_0_to_tester = ['LA17N', 'LA19N', 'LA19P', 'LA20P', 'LA20N', 'LA14N', 'LA14P', 'LA17P', 'LA13N', 'LA13P', 'LA15P', 'LA15N', 'LA16P', 'LA32N', 'LA33P', 'LA33N', 'LA7P', 'LA5P', 'LA7N', 'LA8N', 'LA8P', 'LA6N', 'LA12P', 'LA9N', 'LA16N', 'LA12N', 'LA11P', 'LA10N', 'LA11N', 'LA10P', 'LA9P', 'LA5N']
gpio_1_to_tester = ['LA27P', 'LA23N', 'LA22P', 'LA22N', 'LA18N', 'LA18P', 'LA23P', 'LA21P', 'LA24P', 'LA25N', 'TCK_TO_FMC', 'LA25P', 'LA27N', 'LA26P', 'LA21N', 'LA26N', 'LA32P', 'LA30N', 'GA1', 'LA31N', 'LA30P', 'GA0', 'TRST_TO_FMC', 'TMS_TO_FMC', 'LA29P', 'LA29N', 'TDO_FROM_FMC', 'LA31P', 'LA28N', 'LA28P', 'TDI_TO_FMC', 'LA24N']
gpio_2_to_tester = ['CLK0_M2C_N', 'CLK0_M2C_P', 'PRSNT_M2C_L', 'open', 'open', 'open', 'open', 'open', 'open', 'open', 'open', 'open', 'open', 'open', 'open', 'open', 'M2C_DIR', 'PG_C2M', 'LA1P', 'LA6P', 'LA1N', 'LA3N', 'LA4P', 'LA3P', 'VREF_A_M2C', 'CLK1_M2C_N', 'CLK1_M2C_P', 'LA0P', 'LA2P', 'LA0N', 'LA2N', 'LA4N']

gpio_0_to_FMC = ['D21', 'H23', 'H22', 'G21', 'G22', 'C19', 'C18', 'D20', 'D18', 'D17', 'H19', 'H20', 'G18', 'H38', 'G36', 'G37', 'H13', 'D11', 'H14', 'G13', 'G12', 'C11', 'G15', 'D15', 'G19', 'G16', 'H16', 'C15', 'H17', 'C14', 'D14', 'D12']
gpio_1_to_FMC = ['C26', 'D24', 'G24', 'G25', 'C23', 'C22', 'D23', 'H25', 'H28', 'G28', 'D29', 'G27', 'C27', 'D26', 'H26', 'D27', 'H37', 'H35', 'D35', 'G34', 'H34', 'C34', 'D34', 'D33', 'G30', 'G31', 'D31', 'G33', 'H32', 'H31', 'D30', 'H29']
gpio_2_to_FMC = ['H5', 'H4', 'H2', 'open', 'open', 'open', 'open', 'open', 'open', 'open', 'open', 'open', 'open', 'open', 'open', 'open', 'B1', 'D1', 'D8', 'C10', 'D9', 'G10', 'H10', 'G9', 'H1', 'G3', 'G2', 'G6', 'H7', 'G7', 'H8', 'H11']
  
i2c_addr_to_schematicID = {0x27: 'IC1', 0x24: 'IC2', 0x22: 'IC3', 0x26: 'IC4', 0x21: 'IC5', 0x25: 'IC6'}
	
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
			raise Exception('No ACK upon address (device 0x%x not connected?)' % (addr >> 1))

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

# To be done
#class EEPROM_2AA64T:

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

## To be done
class SWITCH_ADN4600:
        # Only basic mode is implemented
        RST = 0x0;
        XPT_CFG = 0x1;
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
                pass

class EXPANDER_MCP23017:
        IODIRA = 0x0;        IODIRB = 0x01
        IPOLA = 0x02;        IPOLB = 0x03;  
        GPINTENA = 0x04;     GPINTENB = 0x05;  
        DEFVALA = 0x06;      DEFVALB = 0x07; 
        INTCONA = 0x08;      INTCONB = 0x09;  # Shared register between the two ports
        IOCONA = 0x0A;       IOCONB = 0x0B;  
        GPPUA = 0x0C;        GPPUB = 0x0D;
        INTFA = 0x0E;        INTFB = 0x0F;
        INTCAPA = 0x10;      INTCAPB = 0x11;  
        GPIOA = 0x12;        GPIOB = 0x13;       
        OLATA = 0x14;        OLATB = 0x15;

        IOCON_BANK = 7;      IOCON_MIRROR = 6;    IOCON_SEQOP = 5;
        IOCON_DISSLW = 4;    IOCON_HAEN = 3;      IOCON_ODR = 2;        IOCON_INTPOL = 1;

	def __init__(self, i2c, addr):
		self.i2c = i2c;
		self.addr = addr; 
 
                cfg_value = (0 << EXPANDER_MCP23017.IOCON_BANK) + (1 << EXPANDER_MCP23017.IOCON_MIRROR) + (1 << EXPANDER_MCP23017.IOCON_SEQOP) + (1 << EXPANDER_MCP23017.IOCON_DISSLW) + (1 << EXPANDER_MCP23017.IOCON_HAEN) + (0 << EXPANDER_MCP23017.IOCON_ODR) + (1 << EXPANDER_MCP23017.IOCON_INTPOL);
                
                self.i2c.start(self.addr, True);
                self.i2c.write(self.IOCONA, False);
                self.i2c.write(cfg_value, True);
                self.i2c.start(self.addr, True);
                self.i2c.write(self.IOCONB, False);
                self.i2c.write(cfg_value, True);

                # Setup every port as input
                self.i2c.start(self.addr, True);
                self.i2c.write(self.IODIRA, False);
                self.i2c.write(0xFF, True);                                # 1 means input
                self.i2c.start(self.addr, True);
                self.i2c.write(self.IODIRB, False);
                self.i2c.write(0xFF, True);

                # Setup input polarity register
                self.i2c.start(self.addr, True);
                self.i2c.write(self.IPOLA, False);
                self.i2c.write(0x00, True);                                # 0  means no change in polarity at output
                self.i2c.start(self.addr, True);
                self.i2c.write(self.IPOLB, False);
                self.i2c.write(0x00, True);

                # Setup interrupt-on-change control register
                self.i2c.start(self.addr, True);
                self.i2c.write(self.GPINTENA, False);
                self.i2c.write(0x00, True);                                # 0 means no interrupt
                self.i2c.start(self.addr, True);
                self.i2c.write(self.GPINTENB, False);
                self.i2c.write(0x00, True);

                # Setup default comparre register for interrupt-on-change
                self.i2c.start(self.addr, True);
                self.i2c.write(self.GPINTENA, False);
                self.i2c.write(0x00, True);                               # In case that interrupt-on-change is used
                self.i2c.start(self.addr, True);                          # this is the default interrupt msimatch value
                self.i2c.write(self.GPINTENB, False);
                self.i2c.write(0x00, True);
       
                # Setup interrupt control register
                self.i2c.start(self.addr, True);
                self.i2c.write(self.INTCONA, False);
                self.i2c.write(0x00, True);                               # If 0 is select it means that comparison takes places
                self.i2c.start(self.addr, True);                          # against DEFVAL. Otherwise, against last value (OLAT)
                self.i2c.write(self.INTCONB, False);
                self.i2c.write(0x00, True);
      
                # Setup pull-up resistor configuration register
                self.i2c.start(self.addr, True);
                self.i2c.write(self.INTCONA, False);
                self.i2c.write(0xFF, True);                               # 1 means using 100K as pull-up    
                self.i2c.start(self.addr, True);                          
                self.i2c.write(self.INTCONB, False);
                self.i2c.write(0xFF, True);
        
        def set_input(self, bank, boolean):
                self.i2c.start(self.addr, True);
                if (bank == EXPANDER_MCP23017.GPIOA):
                    self.i2c.write(self.IODIRA, False);
                else:
                    self.i2c.write(self.IODIRB, False);
                if (boolean):
                    self.i2c.write(0xFF, True);
                else:
                    self.i2c.write(0x00, True);

        def set_input_masked(self, bank, mask):
                self.i2c.start(self.addr, True);
                if (bank == EXPANDER_MCP23017.GPIOA):
                    self.i2c.write(self.IODIRA, False);
                else:
                    self.i2c.write(self.IODIRB, False);
                self.i2c.write(mask, True);

	def wr_reg8(self, bank, value):
                
		self.i2c.start(self.addr, True); # write cycle
                self.i2c.write(bank, False);
		self.i2c.write(value, True);	

	def rd_reg8(self, bank):
		self.i2c.start(self.addr, True);
		self.i2c.write(bank, False);
		self.i2c.start(self.addr, False);
		return self.i2c.read(True);

class GPIO_slave:
        R_GPIO_DIR     = 0x0
        R_GPIO_IOBUF   = 0x4
        R_GPIO_CTR     = 0x8

        def __init__(self, bus, base):
            self.bus = bus;
            self.base = base;
            if (self.base == BASE_GPIO0):
                self.name = 'GPIO_0'
            elif (self.base == BASE_GPIO1):
#            if (self.base == BASE_GPIO1):
                self.name = 'GPIO_1'
            elif (self.base == BASE_GPIO2):
                self.name = 'GPIO_2'
            self.bus.iwrite(0, self.base +  self.R_GPIO_DIR, 4, 0xFFFFFFFF)

        def rd_GPIO_CTR(self):
            return self.bus.iread(0, self.base +  self.R_GPIO_CTR, 4)

        def set_GPIO_inout(self, value):
            self.bus.iwrite(0, self.base +  self.R_GPIO_DIR, 4, value)

        def wr_GPIO_block(self, value):
            self.bus.iwrite(0, self.base +  self.R_GPIO_DIR, 4, 0x00000000)
            self.bus.iwrite(0, self.base +  self.R_GPIO_IOBUF, 4, value)

        def rd_GPIO_block(self):
            self.bus.iwrite(0, self.base +  self.R_GPIO_DIR, 4, 0xFFFFFFFF)
            return self.bus.iread(0, self.base +  self.R_GPIO_IOBUF, 4)

        def wr_GPIO_block_custom(self, mask, value):
            wr_mask = mask ^ 0xFFFFFFFF
            self.bus.iwrite(0, self.base +  self.R_GPIO_DIR, 4, wr_mask)  # According to IOBUF spec, 0 means write into the pad
            self.bus.iwrite(0, self.base +  self.R_GPIO_IOBUF, 4, value & mask)

        def rd_GPIO_block_custom(self, mask):
            self.bus.iwrite(0, self.base +  self.R_GPIO_DIR, 4, mask)  # According to IOBUF spec, 0 means write into the pad
            value = self.bus.iread(0, self.base +  self.R_GPIO_IOBUF, 4)
            return (value & mask)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise

def FMC_roll_test_CC_16bits(i2c_block, i2c_block_mask, gpio_block, gpio_block_mask, offset, device) :
    print "----------------------------------------"
    print "--  SPEC Manufacturing test suite     --"
    print "----------------------------------------"

    if offset != 0 | offset != 16:
        raise Exception("Bad offset")

    i2c_block.set_input(EXPANDER_MCP23017.GPIOA, 0xFF)
    i2c_block.set_input(EXPANDER_MCP23017.GPIOB, 0xFF)
    gpio_block.set_GPIO_inout(0xFFFFFFFF)
#    print "IODIRA\t" + hex(i2c_block.rd_reg8(EXPANDER_MCP23017.IODIRA))
#    print "IODIRB\t" + hex(i2c_block.rd_reg8(EXPANDER_MCP23017.IODIRB))
    time.sleep(0.1)

    print "\n- Device\t" + device
    print "- Test code\t" + "%.2X"%FMC_SPEC_ROLL_0_TEST_ID_CC_gpio_to_i2c_16bits + "\tRolling one grounded pin among vsuppply pins"
    print "- Additional\tgpio_block_mask:\t" + hex(gpio_block_mask)
    print "Expected:\t" + "Received:\t" + "Mask\t\t" + "Info\t"
#    print "Vector\t\tShortcircuit"
    global groundShorts, vsupplyShorts
    groundShorts = []
    vsupplyShorts = []

    gpio_bank_list = [gpio_block]
    i2c_list = [i2c_block]
    test_id = FMC_SPEC_ROLL_0_TEST_ID_CC_gpio_to_i2c_16bits
    bits_tested = 16
    offset = offset

    for i in range(-1,16):
        if i == -1:
            expected = 0xFFFF
        else:
            expected = 0xFFFF ^ (1 << (i+offset))
        gpio_block.set_GPIO_inout(0x00000000)
        i2c_block.set_input(EXPANDER_MCP23017.GPIOA, 0xFF)
        i2c_block.set_input(EXPANDER_MCP23017.GPIOB, 0xFF)
        expected = expected & gpio_block_mask
        gpio_block.wr_GPIO_block(expected)
        rcv_byte1 = i2c_block.rd_reg8(EXPANDER_MCP23017.GPIOA)
        rcv_byte0 = i2c_block.rd_reg8(EXPANDER_MCP23017.GPIOB)
        received = 0
        received = (rcv_byte1 << 8) | rcv_byte0
        expected = expected >> offset
        header_msg = "%.4X" %expected
        analyse_Shortcircuit(expected, received, gpio_block_mask, 16, header_msg, gpio_block, offset)

# LOOK AT THIS PART!!
    groundShorts = sorted(set(groundShorts))
    vsupplyShorts = sorted(set(vsupplyShorts))


    write_test_results(gpio_bank_list, i2c_list, test_id, bits_tested, offset)

    show_test_results(gpio_block, bits_tested, offset, groundShorts, vsupplyShorts)

    if (len(groundShorts) == 0) & (len(vsupplyShorts) == 0):
        print "---- Test OK!\n"
        testStatus[get_filename(gpio_bank_list, i2c_list)] = 'OK'
    else:
        testStatus[get_filename(gpio_bank_list, i2c_list)] = 'Fail'


    groundShorts = []
    vsupplyShorts = []
    

    print "\n- Device\t" + device
    print "- Test code\t" + "%.2X"%FMC_SPEC_ROLL_1_TEST_ID_CC_gpio_to_i2c_16bits + "\tRolling one vsupply pin among grounded pins"
    print "- Additional\tgpio_block_mask:\t" + hex(gpio_block_mask)
    print "Expected:\t" + "Received:\t" + "Mask\t\t" + "Info\t"
    gpio_block.set_GPIO_inout(0xFFFFFFFF) 
#    print "Vector\t\tShortcircuit"
#    global groundShorts, vsupplyShorts
    groundShorts = []
    vsupplyShorts = []

    gpio_bank_list = [gpio_block]
    i2c_list = [i2c_block]
    test_id = FMC_SPEC_ROLL_1_TEST_ID_CC_gpio_to_i2c_16bits
    bits_tested = 16
    offset = offset

    for i in range(-1,16):
        if i == -1:
            expected = 0x0000
        else:
            expected = 0x0000 ^ (1 << (i+offset))
        gpio_block.set_GPIO_inout(0x00000000)
        i2c_block.set_input(EXPANDER_MCP23017.GPIOA, 0xFF)
        i2c_block.set_input(EXPANDER_MCP23017.GPIOB, 0xFF)
        expected = expected & gpio_block_mask
        gpio_block.wr_GPIO_block(expected)
        rcv_byte1 = i2c_block.rd_reg8(EXPANDER_MCP23017.GPIOA)
        rcv_byte0 = i2c_block.rd_reg8(EXPANDER_MCP23017.GPIOB)
        received = 0
        received = (rcv_byte1 << 8) | rcv_byte0
        expected = expected >> offset
        header_msg = "%.4X" %expected
        analyse_Shortcircuit(expected, received, gpio_block_mask, 16, header_msg, gpio_block, offset)

    groundShorts = sorted(set(groundShorts))
    vsupplyShorts = sorted(set(vsupplyShorts))

    write_test_results(gpio_bank_list, i2c_list, test_id, bits_tested, offset)

    show_test_results(gpio_block, bits_tested, offset, groundShorts, vsupplyShorts)

    if (len(groundShorts) == 0) & (len(vsupplyShorts) == 0):
        print "---- Test OK!\n"
        testStatus[get_filename(gpio_bank_list, i2c_list)] = 'OK'
    else:
        testStatus[get_filename(gpio_bank_list, i2c_list)] = 'Fail'


    groundShorts = []
    vsupplyShorts = []

    i2c_block.set_input(EXPANDER_MCP23017.GPIOA, True)
    i2c_block.set_input(EXPANDER_MCP23017.GPIOB, True)
    gpio_block.set_GPIO_inout(0xFFFFFFFF)

def FMC_roll_test_CC(i2c_block_upper, i2c_block_upper_mask, i2c_block_lower, i2c_block_lower_mask, gpio_block, gpio_block_mask, device) :
    print "----------------------------------------"
    print "--  SPEC Manufacturing test suite     --"
    print "----------------------------------------"

    i2c_block_upper.set_input(EXPANDER_MCP23017.GPIOA, 0xFF)
    i2c_block_upper.set_input(EXPANDER_MCP23017.GPIOB, 0xFF)
    i2c_block_lower.set_input(EXPANDER_MCP23017.GPIOA, 0xFF)
    i2c_block_lower.set_input(EXPANDER_MCP23017.GPIOB, 0xFF)
    gpio_block.set_GPIO_inout(0xFFFFFFFF)
#    print "IODIRA\t" + hex(i2c_block_upper.rd_reg8(EXPANDER_MCP23017.IODIRA))
#    print "IODIRB\t" + hex(i2c_block_upper.rd_reg8(EXPANDER_MCP23017.IODIRB))
#    print "IODIRA\t" + hex(i2c_block_lower.rd_reg8(EXPANDER_MCP23017.IODIRA))
#    print "IODIRB\t" + hex(i2c_block_lower.rd_reg8(EXPANDER_MCP23017.IODIRB))
    time.sleep(0.1)   

    print "\n- Device\t" + device
    print "- Test code\t" + "%.2X"%(FMC_SPEC_ROLL_0_TEST_ID_CC_gpio_to_i2c_32bits) + "\tRolling one grounded pin among vsuppply pins"
    print "- Additional\tgpio_block_mask:\t" + hex(gpio_block_mask)
    print "Expected:\t" + "Received:\t" + "Mask\t\t" + "Info\t"
#    print "Vector\t\tShortcircuit"
    global groundShorts, vsupplyShorts
    groundShorts = []
    vsupplyShorts = []

    gpio_bank_list = [gpio_block]
    i2c_list = [i2c_block_upper, i2c_block_lower]
    test_id = FMC_SPEC_ROLL_0_TEST_ID_CC_gpio_to_i2c_32bits
    bits_tested = 32
    offset = 0
   
    for i in range(-1,32):
        if i == -1:
            expected = 0xFFFFFFFF
        else:
            expected = 0xFFFFFFFF ^ (1 << i)
        gpio_block.set_GPIO_inout(0x00000000)
        i2c_block_upper.set_input(EXPANDER_MCP23017.GPIOA, 0xFF)
        i2c_block_upper.set_input(EXPANDER_MCP23017.GPIOB, 0xFF)
        i2c_block_lower.set_input(EXPANDER_MCP23017.GPIOA, 0xFF)
        i2c_block_lower.set_input(EXPANDER_MCP23017.GPIOB, 0xFF)
        gpio_block.wr_GPIO_block(expected & gpio_block_mask)
        rcv_byte3 = i2c_block_upper.rd_reg8(EXPANDER_MCP23017.GPIOA)
        rcv_byte2 = i2c_block_upper.rd_reg8(EXPANDER_MCP23017.GPIOB)
        rcv_byte1 = i2c_block_lower.rd_reg8(EXPANDER_MCP23017.GPIOA)
        rcv_byte0 = i2c_block_lower.rd_reg8(EXPANDER_MCP23017.GPIOB)
        received = 0
        received = (rcv_byte3 << 24)  | (rcv_byte2 << 16) | (rcv_byte1 << 8) | rcv_byte0
        header_msg = "%.8X" %expected
        analyse_Shortcircuit(expected, received, gpio_block_mask, 32, header_msg, gpio_block, offset)

    groundShorts = sorted(set(groundShorts))
    vsupplyShorts = sorted(set(vsupplyShorts))


    write_test_results(gpio_bank_list, i2c_list, test_id, bits_tested, offset)

    FMCgrounded = []
    FMCvsupplytied = []
    FMCok = []

    gpio_trans_list = []

    if gpio_block.name == 'GPIO_0':
        gpio_trans_list = gpio_0_to_FMC
    elif gpio_block.name == 'GPIO_1':
        gpio_trans_list = gpio_1_to_FMC
    elif gpio_block.name == 'GPIO_2':
        gpio_trans_list = gpio_2_to_FMC
    else:
        raise Exception("Bad 'gpio_block'")

    for i in range(bits_tested):
        if i in groundShorts:
            FMCgrounded.append(gpio_trans_list[i + offset])
        elif i in vsupplyShorts:
            FMCvsupplytied.append(gpio_trans_list[i + offset])
        else:
            FMCok.append(gpio_trans_list[i + offset])

    FMCgrounded = sorted(FMCgrounded)
    FMCvsupplytied = sorted(FMCvsupplytied)
    FMCok = sorted(FMCok)

    groundedPins_string = ''
    vsupplyShorts_string = ''

    for i in FMCgrounded:
        groundedPins_string += i + ", "

    for i in FMCvsupplytied:
        vsupplyShorts_string += i + ", "
    
    if len(groundShorts) != 0:
        groundedPins_string = groundedPins_string[:-2]
        print "---- Grounded pins:\t" + groundedPins_string
    if len(vsupplyShorts) != 0:
        vsupplyShorts_string = vsupplyShorts_string[:-2]
        print "---- Vcc tied pins:\t" + vsupplyShorts_string

    FMCgrounded = []
    FMCvsupplytied = []
    FMCok = []


    print "\n- Device\t" + device
    print "- Test code\t" + "%.2X"%(FMC_SPEC_ROLL_1_TEST_ID_CC_gpio_to_i2c_32bits) + "\tRolling one vsupply pin among grounded pins"
    print "- Additional\tgpio_block_mask:\t" + hex(gpio_block_mask)
    print "Expected:\t" + "Received:\t" + "Mask\t\t" + "Info\t"
    gpio_block.set_GPIO_inout(0xFFFFFFFF) 
#    print "Vector\t\tShortcircuit"
#    global groundShorts, vsupplyShorts
    groundShorts = []
    vsupplyShorts = []

    gpio_bank_list = [gpio_block]
    i2c_list = [i2c_block_upper, i2c_block_lower]
    test_id = FMC_SPEC_ROLL_1_TEST_ID_CC_gpio_to_i2c_32bits
    bits_tested = 32
    offset = 0

    for i in range(-1,32):
        if i == -1:
            expected = 0x00000000
        else:
            expected = 0x00000000 ^ (1 << i)
        gpio_block.set_GPIO_inout(0x00000000)
        i2c_block_upper.set_input(EXPANDER_MCP23017.GPIOA, 0xFF)
        i2c_block_upper.set_input(EXPANDER_MCP23017.GPIOB, 0xFF)
        i2c_block_lower.set_input(EXPANDER_MCP23017.GPIOA, 0xFF)
        i2c_block_lower.set_input(EXPANDER_MCP23017.GPIOB, 0xFF)
        gpio_block.wr_GPIO_block(expected & gpio_block_mask)
        #print "Reading Back\t" + hex(gpio_block.rd_GPIO_block() & gpio_block_mask)
        rcv_byte3 = i2c_block_upper.rd_reg8(EXPANDER_MCP23017.GPIOA)
        rcv_byte2 = i2c_block_upper.rd_reg8(EXPANDER_MCP23017.GPIOB)
        rcv_byte1 = i2c_block_lower.rd_reg8(EXPANDER_MCP23017.GPIOA)
        rcv_byte0 = i2c_block_lower.rd_reg8(EXPANDER_MCP23017.GPIOB)
        received = 0
        received = (rcv_byte3 << 24)  | (rcv_byte2 << 16) | (rcv_byte1 << 8) | rcv_byte0
        header_msg = "%.8X" %expected
        analyse_Shortcircuit(expected, received, gpio_block_mask, 32, header_msg, gpio_block, offset)

    groundShorts = sorted(set(groundShorts))
    vsupplyShorts = sorted(set(vsupplyShorts))

    write_test_results(gpio_bank_list, i2c_list, test_id, bits_tested, offset)

    show_test_results(gpio_block, bits_tested, offset, groundShorts, vsupplyShorts)

    if (len(groundShorts) == 0) & (len(vsupplyShorts) == 0):
        print "---- Test OK!\n"
        testStatus[get_filename(gpio_bank_list, i2c_list)] = 'OK'
    else:
        testStatus[get_filename(gpio_bank_list, i2c_list)] = 'Fail'


    i2c_block_upper.set_input(EXPANDER_MCP23017.GPIOA, True)
    i2c_block_upper.set_input(EXPANDER_MCP23017.GPIOB, True)
    i2c_block_lower.set_input(EXPANDER_MCP23017.GPIOA, True)
    i2c_block_lower.set_input(EXPANDER_MCP23017.GPIOB, True)
    gpio_block.set_GPIO_inout(0xFFFFFFFF)

def FMC_roll_test_CC_16bits_i2c_writing(i2c_block, i2c_block_mask, gpio_block, gpio_block_mask, offset, device) :
    print "----------------------------------------"
    print "--  SPEC Manufacturing test suite     --"
    print "----------------------------------------"

    if offset != 0 | offset != 16:
        raise Exception("Bad offset")

    i2c_block.set_input(EXPANDER_MCP23017.GPIOA, 0xFF)
    i2c_block.set_input(EXPANDER_MCP23017.GPIOB, 0xFF)
    gpio_block.set_GPIO_inout(0xFFFFFFFF)
#    print "IODIRA\t" + hex(i2c_block.rd_reg8(EXPANDER_MCP23017.IODIRA))
#    print "IODIRB\t" + hex(i2c_block.rd_reg8(EXPANDER_MCP23017.IODIRB))
    time.sleep(0.1)

    print "\n- Device\t" + device
    print "- Test code\t" + hex(FMC_SPEC_ROLL_0_TEST_ID_CC_i2c_to_gpio_16bits) + "\tRolling one grounded pin among vsuppply pins"
    print "- Additional\tgpio_block_mask:\t" + hex(gpio_block_mask)
    print "Expected:\t" + "Received:\t" + "Mask\t\t" + "Info\t"
#    print "Vector\t\tShortcircuit"
    global groundShorts, vsupplyShorts
    groundShorts = []
    vsupplyShorts = []   

    gpio_bank_list = [gpio_block]
    i2c_list = [i2c_block]
    test_id = FMC_SPEC_ROLL_0_TEST_ID_CC_i2c_to_gpio_16bits
    bits_tested = 16
    offset = offset

    for i in range(-1,16):
        if i == -1:
            expected = 0xFFFF
        else:
            expected = 0xFFFF ^ (1 << i)

        gpio_block.set_GPIO_inout(0xFFFFFFFF)
        mask_A = ((0xFF00) & i2c_block_mask) >> 8 
        mask_B = (0x00FF) & i2c_block_mask
        i2c_block.set_input(EXPANDER_MCP23017.GPIOA, False)
        i2c_block.set_input(EXPANDER_MCP23017.GPIOB, False)  

        wr_byte1 = (0xFF00 & expected) >> 8
        wr_byte0 = (0x00FF & expected)
        i2c_block.wr_reg8(EXPANDER_MCP23017.GPIOA, wr_byte1)
        i2c_block.wr_reg8(EXPANDER_MCP23017.GPIOB, wr_byte0)

        received = gpio_block.rd_GPIO_block() >> offset

        received = received
        expected = expected & i2c_block_mask
        header_msg = "%.4X" %expected

        gpio_block_mask_tmp = (gpio_block_mask >> offset) & 0x0000FFFF
        analyse_Shortcircuit(expected, received, gpio_block_mask_tmp, 16, header_msg, gpio_block, offset)

    groundShorts = sorted(set(groundShorts))
    vsupplyShorts = sorted(set(vsupplyShorts))

    write_test_results(gpio_bank_list, i2c_list, test_id, bits_tested, offset)

    show_test_results(gpio_block, bits_tested, offset, groundShorts, vsupplyShorts)

    if (len(groundShorts) == 0) & (len(vsupplyShorts) == 0):
        print "---- Test OK!\n"
        testStatus[get_filename(gpio_bank_list, i2c_list)] = 'OK'
    else:
        testStatus[get_filename(gpio_bank_list, i2c_list)] = 'Fail'

    print "\n- Device\t" + device
    print "- Test code\t" + hex(FMC_SPEC_ROLL_1_TEST_ID_CC_i2c_to_gpio_16bits) + "\tRolling one vsupply pin among grounded pins"
    print "- Additional\tgpio_block_mask:\t" + hex(gpio_block_mask)
    print "Expected:\t" + "Received:\t" + "Mask\t\t" + "Info\t"
#    print "Vector\t\tShortcircuit"
#    global groundShorts, vsupplyShorts
    groundShorts = []
    vsupplyShorts = []

    gpio_bank_list = [gpio_block]
    i2c_list = [i2c_block]
    test_id = FMC_SPEC_ROLL_1_TEST_ID_CC_i2c_to_gpio_16bits
    bits_tested = 16
    offset = offset
    
    for i in range(-1,16):
        if i == -1:
            expected = 0x0000
        else:
            expected = 0x0000 ^ (1 << i)

        gpio_block.set_GPIO_inout(0xFFFFFFFF)
        mask_A = ((0xFF00) & i2c_block_mask) >> 8 
        mask_B = (0x00FF) & i2c_block_mask
        i2c_block.set_input(EXPANDER_MCP23017.GPIOA, False)
        i2c_block.set_input(EXPANDER_MCP23017.GPIOB, False)  

        wr_byte1 = (0xFF00 & expected) >> 8
        wr_byte0 = (0x00FF & expected)
        i2c_block.wr_reg8(EXPANDER_MCP23017.GPIOA, wr_byte1)
        i2c_block.wr_reg8(EXPANDER_MCP23017.GPIOB, wr_byte0)

        received = gpio_block.rd_GPIO_block() >> offset

        received = received
        expected = expected & i2c_block_mask
        header_msg = "%.4X" %expected

        gpio_block_mask_tmp = (gpio_block_mask >> offset) & 0x0000FFFF
        analyse_Shortcircuit(expected, received, gpio_block_mask_tmp, 16, header_msg, gpio_block, offset)

    groundShorts_tmp = sorted(set(groundShorts))
    vsupplyShorts_tmp = sorted(set(vsupplyShorts))

    groundShorts = []
    vsupplyShorts = []

#    for index in groundShorts_tmp:
#        print "groundShorts\t" + str(index)
#        groundShorts.append(index + offset)
#    for index in vsupplyShorts_tmp:
#        print "vsupplyShorts\t" + str(index)
#        vsupplyShorts.append(index + offset)


    write_test_results(gpio_bank_list, i2c_list, test_id, bits_tested, offset)

    show_test_results(gpio_block, bits_tested, offset, groundShorts, vsupplyShorts)

    if (len(groundShorts) == 0) & (len(vsupplyShorts) == 0):
        print "---- Test OK!\n"
        testStatus[get_filename(gpio_bank_list, i2c_list)] = 'OK'
    else:
        testStatus[get_filename(gpio_bank_list, i2c_list)] = 'Fail'



    i2c_block.set_input(EXPANDER_MCP23017.GPIOA, True)
    i2c_block.set_input(EXPANDER_MCP23017.GPIOB, True)
    gpio_block.set_GPIO_inout(0xFFFFFFFF)

def FMC_roll_test_CC_i2c_writing(i2c_block_upper, i2c_block_upper_mask, i2c_block_lower, i2c_block_lower_mask, gpio_block, gpio_block_mask, device) :
    print "----------------------------------------"
    print "--  SPEC Manufacturing test suite     --"
    print "----------------------------------------"

    i2c_block_upper.set_input(EXPANDER_MCP23017.GPIOA, 0xFF)
    i2c_block_upper.set_input(EXPANDER_MCP23017.GPIOB, 0xFF)
    i2c_block_lower.set_input(EXPANDER_MCP23017.GPIOA, 0xFF)
    i2c_block_lower.set_input(EXPANDER_MCP23017.GPIOB, 0xFF)
    gpio_block.set_GPIO_inout(0xFFFFFFFF)
#    print "IODIRA\t" + hex(i2c_block_upper.rd_reg8(EXPANDER_MCP23017.IODIRA))
#    print "IODIRB\t" + hex(i2c_block_upper.rd_reg8(EXPANDER_MCP23017.IODIRB))
#    print "IODIRA\t" + hex(i2c_block_lower.rd_reg8(EXPANDER_MCP23017.IODIRA))
#    print "IODIRB\t" + hex(i2c_block_lower.rd_reg8(EXPANDER_MCP23017.IODIRB))
    time.sleep(0.1)

    print "\n- Device\t" + device
    print "- Test code\t" + hex(FMC_SPEC_ROLL_0_TEST_ID_CC_i2c_to_gpio_32bits) + "\tRolling one grounded pin among vsuppply pins"
    print "- Additional\tgpio_block_mask:\t" + hex(gpio_block_mask)
    print "Expected:\t" + "Received:\t" + "Mask\t\t" + "Info\t"
#    print "Vector\t\tShortcircuit"
    global groundShorts, vsupplyShorts
    groundShorts = []
    vsupplyShorts = []

    gpio_bank_list = [gpio_block]
    i2c_list = [i2c_block_upper, i2c_block_lower]
    test_id = FMC_SPEC_ROLL_0_TEST_ID_CC_i2c_to_gpio_32bits
    bits_tested = 32
    offset = 0
    
    for i in range(-1,32):
        if i == -1:
            expected = 0xFFFFFFFF
        else:
            expected = 0xFFFFFFFF ^ (1 << i)

        gpio_block.set_GPIO_inout(0xFFFFFFFF)
        mask_upper_A = ((0xFF00) & i2c_block_upper_mask) >> 8 
        mask_upper_B = (0x00FF) & i2c_block_upper_mask
        mask_lower_A = ((0xFF00) & i2c_block_lower_mask) >> 8 
        mask_lower_B = (0x00FF) & i2c_block_lower_mask
        i2c_block_upper.set_input(EXPANDER_MCP23017.GPIOA, False)
        i2c_block_upper.set_input(EXPANDER_MCP23017.GPIOB, False)
        i2c_block_lower.set_input(EXPANDER_MCP23017.GPIOA, False)
        i2c_block_lower.set_input(EXPANDER_MCP23017.GPIOB, False)   

        wr_byte3 = (0xFF000000 & expected) >> 24
        wr_byte2 = (0x00FF0000 & expected) >> 16
        wr_byte1 = (0x0000FF00 & expected) >> 8
        wr_byte0 = (0x000000FF & expected)
        i2c_block_upper.wr_reg8(EXPANDER_MCP23017.GPIOA, wr_byte3)
        i2c_block_upper.wr_reg8(EXPANDER_MCP23017.GPIOB, wr_byte2)
        i2c_block_lower.wr_reg8(EXPANDER_MCP23017.GPIOA, wr_byte1)
        i2c_block_lower.wr_reg8(EXPANDER_MCP23017.GPIOB, wr_byte0)

        received = gpio_block.rd_GPIO_block()

        received = received
        expected = expected & gpio_block_mask
        header_msg = "%.8X" %expected

        analyse_Shortcircuit(expected, received, gpio_block_mask, 32, header_msg, gpio_block, offset)

    groundShorts = sorted(set(groundShorts))
    vsupplyShorts = sorted(set(vsupplyShorts))

    write_test_results(gpio_bank_list, i2c_list, test_id, bits_tested, offset)

    show_test_results(gpio_block, bits_tested, offset, groundShorts, vsupplyShorts)

    if (len(groundShorts) == 0) & (len(vsupplyShorts) == 0):
        print "---- Test OK!\n"
        testStatus[get_filename(gpio_bank_list, i2c_list)] = 'OK'
    else:
        testStatus[get_filename(gpio_bank_list, i2c_list)] = 'Fail'



    print "\n- Device\t" + device
    print "- Test code\t" + hex(FMC_SPEC_ROLL_1_TEST_ID_CC_i2c_to_gpio_32bits) + "\tRolling one vsupply pin among grounded pins"
    print "- Additional\tgpio_block_mask:\t" + hex(gpio_block_mask)
    print "Expected:\t" + "Received:\t" + "Mask\t\t" + "Info\t"

#    print "Vector\t\tShortcircuit"
#    global groundShorts, vsupplyShorts
    groundShorts = []
    vsupplyShorts = []

    gpio_bank_list = [gpio_block]
    i2c_list = [i2c_block_upper, i2c_block_lower]
    test_id = FMC_SPEC_ROLL_1_TEST_ID_CC_i2c_to_gpio_32bits
    bits_tested = 32
    offset = 0
    
    for i in range(-1,32):
        if i == -1:
            expected = 0x00000000
        else:
            expected = 0x00000000 ^ (1 << i)

        gpio_block.set_GPIO_inout(0xFFFFFFFF)
        mask_upper_A = ((0xFF00) & i2c_block_upper_mask) >> 8 
        mask_upper_B = (0x00FF) & i2c_block_upper_mask
        mask_lower_A = ((0xFF00) & i2c_block_lower_mask) >> 8 
        mask_lower_B = (0x00FF) & i2c_block_lower_mask
        i2c_block_upper.set_input(EXPANDER_MCP23017.GPIOA, False)
        i2c_block_upper.set_input(EXPANDER_MCP23017.GPIOB, False)
        i2c_block_lower.set_input(EXPANDER_MCP23017.GPIOA, False)
        i2c_block_lower.set_input(EXPANDER_MCP23017.GPIOB, False)   

        wr_byte3 = (0xFF000000 & expected) >> 24
        wr_byte2 = (0x00FF0000 & expected) >> 16
        wr_byte1 = (0x0000FF00 & expected) >> 8
        wr_byte0 = (0x000000FF & expected)
        i2c_block_upper.wr_reg8(EXPANDER_MCP23017.GPIOA, wr_byte3)
        i2c_block_upper.wr_reg8(EXPANDER_MCP23017.GPIOB, wr_byte2)
        i2c_block_lower.wr_reg8(EXPANDER_MCP23017.GPIOA, wr_byte1)
        i2c_block_lower.wr_reg8(EXPANDER_MCP23017.GPIOB, wr_byte0)

        received = gpio_block.rd_GPIO_block()

        received = received
        expected = expected & gpio_block_mask
        header_msg = "%.8X" %expected

        analyse_Shortcircuit(expected, received, gpio_block_mask, 32, header_msg, gpio_block, offset)

    
    
    groundShorts = sorted(set(groundShorts))
    vsupplyShorts = sorted(set(vsupplyShorts))

    write_test_results(gpio_bank_list, i2c_list, test_id, bits_tested, offset)

    show_test_results(gpio_block, bits_tested, offset, groundShorts, vsupplyShorts)

    if (len(groundShorts) == 0) & (len(vsupplyShorts) == 0):
        print "---- Test OK!\n"
        testStatus[get_filename(gpio_bank_list, i2c_list)] = 'OK'
    else:
        testStatus[get_filename(gpio_bank_list, i2c_list)] = 'Fail'

    i2c_block_upper.set_input(EXPANDER_MCP23017.GPIOA, True)
    i2c_block_upper.set_input(EXPANDER_MCP23017.GPIOB, True)
    i2c_block_lower.set_input(EXPANDER_MCP23017.GPIOA, True)
    i2c_block_lower.set_input(EXPANDER_MCP23017.GPIOB, True)
    gpio_block.set_GPIO_inout(0xFFFFFFFF)

#Needs rework here
def analyse_Shortcircuit(expected, received, mask, amountOfPins, header_msg, gpio_bank, offset):
    discrepancies = expected ^ received
    tmp_groundShorts = []
    tmp_vsupplyShorts = []
    global groundShorts, vsupplyShorts
    for i in xrange(amountOfPins):
        if ((mask & (1 << i)) == 0):
            pass
        elif ((discrepancies & (1 << i)) == (1 << i)):
            #Discrepancy detected at position i
            if ((expected & (1 << i)) == (1 << i)):
                #It was a ground short
                tmp_groundShorts.append(i)
                groundShorts.append(i)
            else:
                #It was vsupply short
                tmp_vsupplyShorts.append(i)
                vsupplyShorts.append(i)

    FMCgrounded = []
    FMCvsupplytied = []
    FMCok = []

    groundedPins_string = ''
    vsupplyShorts_string = ''

    if gpio_bank.name == 'GPIO_0':
        gpio_trans_list = gpio_0_to_FMC
    elif gpio_bank.name == 'GPIO_1':
        gpio_trans_list = gpio_1_to_FMC
    elif gpio_bank.name == 'GPIO_2':
        gpio_trans_list = gpio_2_to_FMC
    else:
        raise Exception("Bad 'gpio_block'")

    for i in range(amountOfPins):
        if i in groundShorts:
            FMCgrounded.append(gpio_trans_list[i + offset])
        elif i in vsupplyShorts:
            FMCvsupplytied.append(gpio_trans_list[i + offset])
        else:
            FMCok.append(gpio_trans_list[i + offset])

    FMCgrounded = sorted(FMCgrounded)
    FMCvsupplytied = sorted(FMCvsupplytied)
    FMCok = sorted(FMCok)

    for i in FMCgrounded:
        groundedPins_string += i + ", "

    for i in FMCvsupplytied:
        vsupplyShorts_string += i + ", "
    
    if len(tmp_groundShorts) != 0:
        groundedPins_string = groundedPins_string[:-2]
    if len(tmp_vsupplyShorts) != 0:
        vsupplyShorts_string = vsupplyShorts_string[:-2]

    if len(tmp_groundShorts) == 0 | len(tmp_vsupplyShorts) == 0: 
        print "%0.8X"%expected + "\t%0.8X"%received + "\t%0.8X"%mask + "\tTest OK!"
    elif len(tmp_groundShorts) != 0:
        print "%0.8X"%expected + "\t%0.8X"%received + "\t%0.8X"%mask + "\tGrounded pins:\t" + groundedPins_string
    elif len(tmp_vsupplyShorts) != 0:
        print "%0.8X"%expected + "\t%0.8X"%received + "\t%0.8X"%mask + "\tVcc tied pins:\t" + vsupplyShorts_string

    #Just to improve human-readabilty
    groundShorts.reverse()
    vsupplyShorts.reverse()

#    if (len(groundShorts) != 0):
#        print header_msg + "\tYes\tGround shorts in pins:\t" + str(groundShorts);
#    
#    if (len(vsupplyShorts) != 0):
#        print header_msg + "\tYes\tVCC shorts in pins:\t" + str(vsupplyShorts);
#
#    if ( (len(groundShorts) == 0) & (len(vsupplyShorts) == 0)):
#        print header_msg + "\tNo"
#        return
        
    #else:
    #    raise Exception("Shortcircuits detected!")


def get_filename(gpio_bank_list, i2c_list):
    filename = ''
    for k in sorted(gpio_bank_list):
        filename += '_' + k.name
    for l in sorted(i2c_list):
        filename += '_' + i2c_addr_to_schematicID[l.addr]
    return filename

def show_test_results(gpio_bank, bits_tested, offset, groundShorts, vsupplyShorts):

    if (offset == 0):
        if (bits_tested != 16 | bits_tested != 32 | bits_tested != 64 | bits_tested != 96 ):
            raise Exception("show_test_results: 'offset' and 'bits_tested' mismatch")
        else:
            pass
    if (offset == 16):
        if (bits_tested != 16):
            raise Exception("show_test_results: 'offset' and 'bits_tested' mismatch")
        else:
            pass
    
    if (offset != 0 | offset != 16):
            raise Exception("show_test_results: bad 'offset'")

    FMCgrounded = []
    FMCvsupplytied = []
    FMCok =  []

    groundedPins_string = ""
    vsupplyShorts_string = ""
    okPins_string = ""

    gpio_trans_list = []

    if gpio_bank.name == 'GPIO_0':
        gpio_trans_list = gpio_0_to_FMC
    elif gpio_bank.name == 'GPIO_1':
        gpio_trans_list = gpio_1_to_FMC
    elif gpio_bank.name == 'GPIO_2':
        gpio_trans_list = gpio_2_to_FMC
    else:
        raise Exception("Bad 'gpio_block'")

    for i in range(bits_tested):
        if i in groundShorts:
            FMCgrounded.append(gpio_trans_list[i + offset])
        elif i in vsupplyShorts:
            FMCvsupplytied.append(gpio_trans_list[i + offset])
        else:
            FMCok.append(gpio_trans_list[i + offset])

    FMCgrounded = sorted(FMCgrounded)
    FMCvsupplytied = sorted(FMCvsupplytied)
    FMCok = sorted(FMCok)

    for i in FMCgrounded:
        groundedPins_string += i + ", "

    for i in FMCvsupplytied:
        vsupplyShorts_string += i + ", "
    
    if len(groundShorts) != 0:
        groundedPins_string = groundedPins_string[:-2]
        print "---- Grounded pins:\t" + groundedPins_string
    if len(vsupplyShorts) != 0:
        vsupplyShorts_string = vsupplyShorts_string[:-2]
        print "---- Vcc tied pins:\t" + vsupplyShorts_string

def summary_results(testStatus):

    loopback_log = os.path.join(default_log_path, './log/test_fmc/loopback/')
    mkdir_p(loopback_log)

    string = ''

    for i in sorted(testStatus.keys()):
        string_tmp = '   ' + i.replace('_', ' ') + '                   '
        string += string_tmp[:30] + testStatus[i] + "\n"
   
    for i in sorted(testStatus.keys()):
        if testStatus[i] == 'Fail':
            raise TpsError("FMC connector failure")
    
    print string 

    filename = "Summary_FMC_tets.txt"

    file = open(os.path.join(loopback_log, filename), 'w')
    file.write(string)
    

def write_test_results(gpio_bank_list, i2c_list, test_id, bits_tested, offset):
    # We store data in log subfolder
    fmc_pinout_log = os.path.join(default_log_path, './log/test_fmc/loopback/FMC_pinout')
    mkdir_p(fmc_pinout_log)

    if (offset == 0):
        if (bits_tested != 16 | bits_tested != 32 | bits_tested != 64 | bits_tested != 96 ):
            raise Exception("write_test_results: 'offset' and 'bits_tested' mismatch")
        else:
            pass
    if (offset == 16):
        if (bits_tested != 16):
            raise Exception("write_test_results: 'offset' and 'bits_tested' mismatch")
        else:
            pass
    
    if (offset != 0 | offset != 16):
            raise Exception("write_test_results: bad 'offset'")

    number_of_gpios = len(gpio_bank_list)

#    if number_of_gpios != (bits_tested/32):
#        raise Exception("'bits_tested' are incompatible with GPIO assigment")

    filename = "FMC"

#    print "offset:\t" + str(offset)

    filename += get_filename(gpio_bank_list, i2c_list)
 
    filename += '_' + "%.2X"%test_id+'.txt' 

# This file generation must be revised !!!
# yes indeed!!! jdgc
    gpio_pinout = os.path.join(tests_path, './log/test_fmc/loopback/GPIO_pinout/')
    mkdir_p(gpio_pinout)
    file = open(os.path.join(gpio_pinout, filename), 'w')
    file.write('DEVICE_ID:\t'+filename[:-7].replace('GPIO_', 'GPIO').replace('_',' ')+'\n')
    file.write('TEST_ID:\t'+"%.2X"%test_id+'\n')
    file.write('OUTPUT_MODE:\t'+'GPIO pinout'+'\n')
    file.write('Pin\t\tStatus'+'\n')
    
    for k in range(number_of_gpios-1, -1, -1):
        file.write('--' + gpio_bank_list[k].name +'\n')
        for i in range(bits_tested+offset-1, offset-1, -1):
            if ((i + 32*k) in groundShorts and (i + 32*k) in vsupplyShorts):
                file.write(str(i)+'\t\tShortcircuit'+'\n')
            elif ((i + 32*k) in groundShorts):
                file.write(str(i)+'\t\tGrounded'+'\n')
            elif ((i + 32*k) in vsupplyShorts):
                file.write(str(i)+'\t\tVCC tied'+'\n')
            else:
                file.write(str(i)+'\t\tOK'+'\n')
    file.close()

    tester_pinout = os.path.join(tests_path, './log/test_fmc/loopback/tester_pinout/')
    mkdir_p(tester_pinout)
    file = open(os.path.join(tester_pinout, filename), 'w')
    file.write('DEVICE_ID:\t'+filename[:-7].replace('GPIO_', 'GPIO').replace('_',' ')+'\n')
    file.write('TEST_ID:\t'+"%.2X"%test_id+'\n')
    file.write('OUTPUT_MODE:\t'+'Tester pinout'+'\n')
    file.write('Pin\t\tStatus'+'\n')

    gpio_order = []

    for k in xrange(number_of_gpios):
        if gpio_bank_list[k].name == 'GPIO_0':
            gpio_order.append(gpio_0_to_tester)
        elif gpio_bank_list[k].name == 'GPIO_1':
            gpio_order.append(gpio_1_to_tester)
        elif gpio_bank_list[k].name == 'GPIO_2':
            gpio_order.append(gpio_2_to_tester)
        else:
            raise Exception("Bad 'gpio_block_name_list'")
   
    for k in xrange(number_of_gpios):
        translation_dict = {}
        for i in range(bits_tested+offset-1,offset-1,-1):
            if (i in groundShorts and i in vsupplyShorts):
                translation_dict[gpio_order[k][i]] = 'Shortcircuit'
            elif (i in groundShorts):
                translation_dict[gpio_order[k][i]] = 'Grounded'
            elif (i in vsupplyShorts):
                translation_dict[gpio_order[k][i]] = 'VCC tied'
            else:
                translation_dict[gpio_order[k][i]] = 'OK'

        file.write('--' + gpio_bank_list[k].name +'\n')
        for k in sorted(translation_dict.keys()):
            file.write(k +'\t\t'+translation_dict[k]+'\n')
    file.close()

    gpio_order = []

    for k in xrange(number_of_gpios):
        if gpio_bank_list[k].name == 'GPIO_0':
            gpio_order.append(gpio_0_to_FMC)
        elif gpio_bank_list[k].name == 'GPIO_1':
            gpio_order.append(gpio_1_to_FMC)
        elif gpio_bank_list[k].name == 'GPIO_2':
            gpio_order.append(gpio_2_to_FMC)
        else:
            raise Exception("Bad 'gpio_block_name_list'")

    file = open(os.path.join(fmc_pinout_log, filename), 'w')
    file.write('DEVICE_ID:\t'+filename[:-7].replace('GPIO_', 'GPIO').replace('_',' ')+'\n')
    file.write('TEST_ID:\t'+"%.2X"%test_id+'\n')
    file.write('OUTPUT_MODE:\t'+'FMC pinout'+'\n')
    file.write('Pin\t\tStatus'+'\n')
    translation_dict = {}

    for k in xrange(number_of_gpios):
        for i in range(bits_tested+offset-1,offset-1,-1):
            if (i in groundShorts and i in vsupplyShorts):
                translation_dict[gpio_order[k][i]] = 'Shortcircuit'
            elif (i in groundShorts):
                translation_dict[gpio_order[k][i]] = 'Grounded'
            elif (i in vsupplyShorts):
                translation_dict[gpio_order[k][i]] = 'VCC tied'
            else:
                translation_dict[gpio_order[k][i]] = 'OK'

    for k in sorted(translation_dict.keys()):
        file.write(k +'\t\t'+translation_dict[k]+'\n')
    file.close()

def main (default_directory='.', default_log='.'):

    global default_log_path, tests_path
    tests_path = default_directory
    default_log_path = default_log
    path_fpga_loader = '../firmwares/fpga_loader';
    path_firmware = '../firmwares/test01.bin';
    	
    firmware_loader = os.path.join(default_directory, path_fpga_loader)
    bitstream = os.path.join(default_directory, path_firmware)
    os.system( firmware_loader + ' ' + bitstream)

    time.sleep(2);
 
    gennum = rr.Gennum();
 
   
    GPIO_BLOCK_0_MASK = 0xFFFFFFFF     # Take care! Here 1 means write into the pad
    GPIO_BLOCK_1_MASK = 0xBB1BFBFF
    GPIO_BLOCK_2_MASK = 0x80FC0000  

    gpio_block_0 = GPIO_slave(gennum, BASE_GPIO0);    # It corresponds to 0x27 and 0x24 I2C addresses
    gpio_block_1 = GPIO_slave(gennum, BASE_GPIO1);    # It corresponds to 0x22 and 0x26 I2C addresses
    gpio_block_2 = GPIO_slave(gennum, BASE_GPIO2);    # It corresponds to 0x22 and 0x26 I2C addresses

    i2c_B = COpenCoresI2C(gennum, BASE_I2C_B, 99);

    expander_IC1 = EXPANDER_MCP23017(i2c_B, 0x27);    expander_IC1_MASK = 0xFFFF
    expander_IC2 = EXPANDER_MCP23017(i2c_B, 0x24);    expander_IC2_MASK = 0xFFFF
    expander_IC3 = EXPANDER_MCP23017(i2c_B, 0x22);    expander_IC3_MASK = 0xBB1B
    expander_IC4 = EXPANDER_MCP23017(i2c_B, 0x26);    expander_IC4_MASK = 0xFBFF
    expander_IC5 = EXPANDER_MCP23017(i2c_B, 0x21);    expander_IC5_MASK = 0x80FC
    expander_IC6 = EXPANDER_MCP23017(i2c_B, 0x25);    expander_IC6_MASK = 0x0000

    # This four lines are gor testing porpouses
    #groundShorts = []
    #vsupplyShorts = []
    #analyse_Shortcircuit(0xFBFBAABB, 0xDEADBABE, 0xFFFFFFFF, 32, "GPIO 1")
    #write_test_results([gpio_block_1], [expander_IC3, expander_IC4], FMC_SPEC_ROLL_0_TEST_ID_CC_gpio_to_i2c_32bits, 32, 0)
    #groundShorts = []
    #vsupplyShorts = []
    #analyse_Shortcircuit(0xFFFF, 0xBABE, 0xFFFF, 16, "GPIO 1")
    #write_test_results([gpio_block_1], [expander_IC3], FMC_SPEC_ROLL_0_TEST_ID_CC_gpio_to_i2c_16bits, 16, 0)

    FMC_roll_test_CC_16bits_i2c_writing(expander_IC1, expander_IC1_MASK, gpio_block_0, GPIO_BLOCK_0_MASK, 16, 'GPIO_0')
    FMC_roll_test_CC_16bits_i2c_writing(expander_IC2, expander_IC2_MASK, gpio_block_0, GPIO_BLOCK_0_MASK, 0, 'GPIO_0')
    FMC_roll_test_CC_16bits_i2c_writing(expander_IC3, expander_IC3_MASK, gpio_block_1, GPIO_BLOCK_1_MASK, 16, 'GPIO_1')
    FMC_roll_test_CC_16bits_i2c_writing(expander_IC4, expander_IC4_MASK, gpio_block_1, GPIO_BLOCK_1_MASK, 0, 'GPIO_1')
    FMC_roll_test_CC_16bits_i2c_writing(expander_IC5, expander_IC5_MASK, gpio_block_2, GPIO_BLOCK_2_MASK, 16, 'GPIO_2')
    FMC_roll_test_CC_16bits_i2c_writing(expander_IC6, expander_IC6_MASK, gpio_block_2, GPIO_BLOCK_2_MASK, 0, 'GPIO_2')

    FMC_roll_test_CC_i2c_writing(expander_IC1, expander_IC1_MASK, expander_IC2, expander_IC2_MASK, gpio_block_0, GPIO_BLOCK_0_MASK, 'GPIO_0')
    FMC_roll_test_CC_i2c_writing(expander_IC3, expander_IC3_MASK, expander_IC4, expander_IC4_MASK, gpio_block_1, GPIO_BLOCK_1_MASK, 'GPIO_1')
    FMC_roll_test_CC_i2c_writing(expander_IC5, expander_IC5_MASK, expander_IC6, expander_IC6_MASK, gpio_block_2, GPIO_BLOCK_2_MASK, 'GPIO_2')

    FMC_roll_test_CC_16bits(expander_IC1, expander_IC1_MASK, gpio_block_0, GPIO_BLOCK_0_MASK, 16, 'GPIO_0')
    FMC_roll_test_CC_16bits(expander_IC2, expander_IC2_MASK, gpio_block_0, GPIO_BLOCK_0_MASK, 0, 'GPIO_0')
    FMC_roll_test_CC_16bits(expander_IC3, expander_IC3_MASK, gpio_block_1, GPIO_BLOCK_1_MASK, 16, 'GPIO_1')
    FMC_roll_test_CC_16bits(expander_IC4, expander_IC4_MASK, gpio_block_1, GPIO_BLOCK_1_MASK, 0, 'GPIO_1')
    FMC_roll_test_CC_16bits(expander_IC5, expander_IC5_MASK, gpio_block_2, GPIO_BLOCK_2_MASK, 16, 'GPIO_2')
    FMC_roll_test_CC_16bits(expander_IC6, expander_IC6_MASK, gpio_block_2, GPIO_BLOCK_2_MASK, 0, 'GPIO_2')

    FMC_roll_test_CC(expander_IC1, expander_IC1_MASK, expander_IC2, expander_IC2_MASK, gpio_block_0, GPIO_BLOCK_0_MASK, 'GPIO_0')
    FMC_roll_test_CC(expander_IC3, expander_IC3_MASK, expander_IC4, expander_IC4_MASK, gpio_block_1, GPIO_BLOCK_1_MASK, 'GPIO_1')
    FMC_roll_test_CC(expander_IC5, expander_IC5_MASK, expander_IC6, expander_IC6_MASK, gpio_block_2, GPIO_BLOCK_2_MASK, 'GPIO_2')

    summary_results(testStatus)

groundShorts  = []
vsupplyShorts = []
if __name__ == '__main__':
	main(default_directory='.', default_log='.')
