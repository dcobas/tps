#!   /usr/bin/env   python
#    coding: utf8

import sys
import rr
import time
import os

"""
test02: checks the EEPROM of the GENNUM chip.
"""

class EEPROM_GENNUM:

    LB_CTL = 0x804;
    TWI_CTRL = 0x900;
    TWI_STATUS = 0x904;
    TWI_IRT_STATUS = 0x910;
    I2C_ADDR = 0x908;
    I2C_DATA = 0x90C;

    def __init__ (self, gennum):
        self.gennum = gennum;

    def i2c_read(self, i2c_addr, offset, length, read_data):
        """Read from I2C
        """

        # Shut off EEPROM_INIT state machine if not done so */
        tmp = self.gennum.iread(4, self.LB_CTL, 4)
        #print 'LB_CTL=%.8X' % tmp
        if tmp & 0x10000 == 0:
            tmp |= 0x10000
            self.gennum.iwrite(4, self.LB_CTL, 4, tmp)

        # Init I2C clock Fpci/(22*Fscl)=(DIV_A+1)*(DIV_B+1)
        # CLR_FIFO=1, SLVMON=0, HOLD=0, ACKEN=1, NEA=1, MS=1, RW=0
        self.gennum.iwrite(4, self.TWI_CTRL, 4, 0x384E)
        # Read back from register to guarantee the mode change
        tmp = self.gennum.iread(4, self.TWI_CTRL, 4)

        # Wait until I2C bus is idle
        i=2000000
        while i > 0:
            i-=1
            tmp = self.gennum.iread(4, self.TWI_STATUS, 4)
            #print 'TWI_STATUS=%.8X' % tmp
            #time.sleep(.5)
            if tmp & 0x100 == 0:
                #print 'I2C bus is idle'
                break

        # Read to clear TWI_IRT_STATUS
        tmp = self.gennum.iread(4, self.TWI_IRT_STATUS, 4)
        # Write word offset
        tmp=(0xFF & offset)
        self.gennum.iwrite(4, self.I2C_DATA, 4, tmp)

        # Write device address
        tmp=(0x7F & i2c_addr)
        self.gennum.iwrite(4, self.I2C_ADDR, 4, tmp)

        # Wait for transfer complete status
        i=2000000
        while i > 0:
            tmp = self.gennum.iread(4, self.TWI_IRT_STATUS, 4)
            if tmp & 0x1:
                break
            elif tmp & 0xC:
                raise TpsError ('NACK detected or TIMEOUT, IRT_STATUS = 0x%x!!' % tmp)
                sys.exit()
            i-=1
        if i == 0:
            raise TpsError ('ERROR, completion status not detected!!')
            sys.exit()

        # Change to read mode
        self.gennum.iwrite(4, self.TWI_CTRL, 4, 0x384F)
        # Perform sequential page read from the start address
        error_flag=0
        total_transfer=0
        while length > 0 and error_flag == 0:
            # Transfer bigger than I2C fifo (8 bytes) are split
            if length > 8:
                transfer_len = 8
                length -= 8
            else:
                transfer_len = length
                length = 0
            # Update expected receive data size
            self.gennum.iwrite(4, 0x914, 4, transfer_len)
            # Write device address
            self.gennum.iwrite(4, self.I2C_ADDR, 4, (0x7F & i2c_addr))
            # Wait until transfer is completed
            j=2000000
            while j > 0:
                tmp = self.gennum.iread(4, self.TWI_IRT_STATUS, 4)
                if tmp & 0x1:
                    #print 'Transfer completed'
                    break
                j-=1
            if j == 0:
                error_flag = 1
                raise TpsWarning('ERROR, completion status not detected!!')
            # Read data from fifo
            while transfer_len > 0:
                read_data.append(0xFF & self.gennum.iread(4, self.I2C_DATA, 4))
                transfer_len-=1
                total_transfer+=1
        # End of read
        return total_transfer

    # 
    def i2c_write(self, i2c_addr, offset, length, write_data):
        """Write to I2C
        """

        # Shut off EEPROM_INIT state machine if not done so */
        tmp = self.gennum.iread(4, self.LB_CTL, 4)
        if tmp & 0x10000 == 0:
            tmp |= 0x10000
            self.gennum.iwrite(4, self.LB_CTL, 4, tmp)

        # Read to clear TWI_IRT_STATUS
        self.gennum.iread(4, self.TWI_IRT_STATUS, 4)
        # Read to clear TWI_STATUS
        self.gennum.iread(4, self.TWI_STATUS, 4)
        # Init I2C clock Fpci/(22*Fscl)=(DIV_A+1)*(DIV_B+1)
        # CLR_FIFO=1, SLVMON=0, HOLD=0, ACKEN=1, NEA=1, MS=1, RW=0
        self.gennum.iwrite(4, self.TWI_CTRL, 4, 0x384E)
        # Read back from register to guarantee the mode change
        self.gennum.iread(4, self.TWI_CTRL, 4)
        # Wait until I2C bus is idle
        i=2000000
        while i > 0:
            i-=1
            tmp = self.gennum.iread(4, self.TWI_STATUS, 4)
            if tmp & 0x100 == 0:
                break
        # Perform sequential page write from the start address
        error_flag=0
        total_transfer=0
        while length > 0 and error_flag == 0:
            # Write word offset
            self.gennum.iwrite(4, self.I2C_DATA, 4, (0xFF & offset))
            i=6 # fifo size - 2
            while i > 0 and length > 0:
                tmp = (0xFF & write_data[total_transfer])
                self.gennum.iwrite(4, self.I2C_DATA, 4, tmp)
                total_transfer+=1
                offset+=1
                i-=1
                length-=1
                # Reaches the page write address boundary, thus need to start
                # the offset at the next page (page size = 8)
                if offset & 7 == 0:
                    break
            # Write device address
            self.gennum.iwrite(4, self.I2C_ADDR, 4, (0x7F & i2c_addr))
            #print 'Write I2C address'
            # Wait until transfer is completed
            i=2000000
            while i > 0:
                tmp = self.gennum.iread(4, self.TWI_IRT_STATUS, 4)
                time.sleep(0.01)
                if tmp & 0x1:
                    #print 'Transfer completed!'
                    tmp = self.gennum.iread(4, 0x914, 4)
                    #print 'TR_SIZE=%d' % tmp
                    break
                elif tmp & 0xC:
                    raise TpsWarning ('NACK detected or TIMEOUT, IRT_STATUS = 0x%x!!' % tmp)
                    tmp = self.gennum.iread(4, 0x914, 4)
                    return total_transfer
                i-=1
        return total_transfer

    def eeprom_dump_to_screen(self):
        """ Dump the content of the EEPROM to the screen
        """  

        eeprom_data=[]
        nb_rec=42
        self.i2c_read(0x56, 0, nb_rec*6, eeprom_data)
        for i in range(0,nb_rec*6,6):
            addr=eeprom_data[i] + (eeprom_data[i+1] << 8)
            data=eeprom_data[i+2] + (eeprom_data[i+3] << 8) + (eeprom_data[i+4] << 16) + (eeprom_data[i+5] << 24)
            if addr == 0xFFFF:
                break
            print '[%.2d]=%.4X %.8X' %(i/6,addr,data)
        print ''
        for i in range(0,len(eeprom_data)):
            print '[%.2d]=%.2X' %(i,eeprom_data[i])
            if eeprom_data[i+1] == 0xFF and eeprom_data[i+2] == 0xFF:
                break
        return 0

    def eeprom_dump_to_file(self, file_name):
        """Dump the content of the EEPROM to a file
        """

        if file_name == "":
            file_name = "eeprom.dat"
        file = open(file_name, 'w+')
        eeprom_data=[]
        nb_rec=100
        self.i2c_read(0x56, 0, nb_rec*6, eeprom_data)
        for i in range(0,nb_rec*6,6):
            addr=eeprom_data[i] + (eeprom_data[i+1] << 8)
            data=eeprom_data[i+2] + (eeprom_data[i+3] << 8) + (eeprom_data[i+4] << 16) + (eeprom_data[i+5] << 24)
            print >>file,'%.4X %.8X' %(addr,data)
            if addr == 0xFFFF:
                break
        return 0

    def file_dump_to_screen(self, file_name):
        """Dump the content of a file to the screen
        """
        if file_name == "":
            file_name = "eeprom.dat"
        file = open(file_name, 'r+')
        file_data=[]
        for line in file:
            addr,data = line.split()
            print addr+' '+data
            for i in range(2,0,-1):
                #print addr[(i-1)*2:(i-1)*2+2]
                file_data.append(int(addr[(i-1)*2:(i-1)*2+2],16))
            for i in range(4,0,-1):
                #print data[(i-1)*2:(i-1)*2+2]
                file_data.append(int(data[(i-1)*2:(i-1)*2+2],16))
        print ''
        for i in range(0,len(file_data)):
            print '[%.2d]=%.2X' %(i,file_data[i])
        return 0

    def file_dump_to_eeprom(self, file_name):
        """Dump the content of a file to the EEPROM
        """
        if file_name == "":
            file_name = "eeprom.dat"
        file = open(file_name, 'r+')
        file_data=[]
        # Read file
        for line in file:
            addr,data = line.split()
            for i in range(2,0,-1):
                #print addr[(i-1)*2:(i-1)*2+2]
                file_data.append(int(addr[(i-1)*2:(i-1)*2+2],16))
            for i in range(4,0,-1):
                #print data[(i-1)*2:(i-1)*2+2]
                file_data.append(int(data[(i-1)*2:(i-1)*2+2],16))
        # Write EEPROM
        #print len(file_data)
        #print file_data
        written = self.i2c_write(0x56, 0, len(file_data), file_data)
        if written == len(file_data):
            print 'EEPROM written with '+file_name+' content!'
        else :
            raise TpsUser ("ERROR writting to the EEPROM: Written lenght doesn't correspond with the length of the file.")
        return 0

    def compare_eeprom_with_file(self, file_name):
        """Compare the content of a file to the EEPROM
        """

        if file_name == "":
            file_name = "eeprom.dat"
        file = open(file_name, 'r+')
        file_data=[]
        eeprom_data=[]
        nb_rec=0
        # Read file
        for line in file:
            addr,data = line.split()
            for i in range(2,0,-1):
                #print addr[(i-1)*2:(i-1)*2+2]
                file_data.append(int(addr[(i-1)*2:(i-1)*2+2],16))
            for i in range(4,0,-1):
                #print data[(i-1)*2:(i-1)*2+2]
                file_data.append(int(data[(i-1)*2:(i-1)*2+2],16))
            nb_rec+=1
        # Read EEPROM
        self.i2c_read(0x56, 0, (nb_rec+1)*6, eeprom_data)
        # Compare
        for i in range(0,len(file_data)):
            if file_data[i] == eeprom_data[i]:
                print 'EEPROM= %.2X, FILE= %.2X => OK' %(eeprom_data[i],file_data[i])
            else :
                raise TpsUser('EEPROM= %.2X, FILE= %.2X => ERROR' %(eeprom_data[i],file_data[i]))

def main (default_directory='.'):

    path_fpga_loader = '../firmwares/fpga_loader';
    path_firmware = '../firmwares/test02.bin';
    	
    firmware_loader = os.path.join(default_directory, path_fpga_loader)
    bitstream = os.path.join(default_directory, path_firmware)
    os.system( firmware_loader + ' ' + bitstream)

    time.sleep(2);

    gennum = rr.Gennum();
    eeprom = EEPROM_GENNUM(gennum);
    eeprom.eeprom_dump_to_file("/tmp/eeprom.dat"); 

    eeprom.file_dump_to_eeprom(default_directory+"/eeprom_test_A.dat");
    eeprom.eeprom_dump_to_screen();
    eeprom.compare_eeprom_with_file(default_directory +"/eeprom_test_A.dat");

    eeprom.file_dump_to_eeprom("/tmp/eeprom.dat");
    eeprom.eeprom_dump_to_screen();
    eeprom.compare_eeprom_with_file("/tmp/eeprom.dat");

if __name__ == '__main__' :
	main();
