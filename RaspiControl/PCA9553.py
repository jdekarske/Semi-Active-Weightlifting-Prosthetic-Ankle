# Distributed with a free-will license.
# Use it any way you want, profit or free, provided it fits in the licenses of its associated works.
# 
# Datasheet: https://www.nxp.com/docs/en/data-sheet/PCA9553.pdf
# www.jasondekarske.com
import smbus
import time


class PCA9553:

    # Control registers
    PSC0                = 0X1
    PWM0                = 0X2
    PSC1                = 0X3
    PWM1                = 0X4
    LS0	                = 0X5
    CHGREEN             = 0
    CHRED               = 1
    CHBLUE              = 2

    def __init__(self, address=0x62):
        self._address = address
        self.ledbits = 0
    
    def begin(self, blinkspeed=.5 ):
        self._bus = smbus.SMBus(1) # Set some defaults
        self.setBlink(0,blinkspeed) # time between blinks
        self.setBlink(1,blinkspeed)
        self.setPWM(0,50)   # blink length (%)
        self.setPWM(1,50)
        self.setLED(PCA9553.CHBLUE,1)    # turn LEDs off to start
        self.setLED(PCA9553.CHGREEN,1)
        self.setLED(PCA9553.CHRED,1)
        self.go()
        
    def setPWM(self, mode, dutycycle):  # blink length (%)
        if mode:
            mode = PCA9553.PWM1
        else:
            mode = PCA9553.PWM0
        dutycycle = int(256-dutycycle*256/100)
        self.writeBytes(mode, dutycycle)

    def setBlink(self, mode, period):   # blink rate (Hz)
        if mode:
            mode = PCA9553.PSC1
        else:
            mode = PCA9553.PSC0
        period = int(period*24-1)
        self.writeBytes(mode, period)

    def setLED(self, channel, mode):    # 0-on, 1-off, 2-PWM0, 3-PWM1
        self.ledbits &= ~(3<<(channel*2))   # yikes
        self.ledbits |= mode<<(channel*2)

    def go(self):
        self.writeBytes(PCA9553.LS0,self.ledbits)

    def readBytes(self, register, numBytes=1):
        return self._bus.read_i2c_block_data(self._address, register, numBytes)

    def writeBytes(self, register, byteVals):
        #print(bin((register<<8)|byteVals))
        return self._bus.write_byte_data(self._address, register, byteVals)


if __name__ == '__main__': # example, should blink purple
	pca = PCA9553()
	pca.begin()
	pca.setLED(PCA9553.CHRED,3)
        pca.setLED(PCA9553.CHBLUE,2)
        pca.go()
