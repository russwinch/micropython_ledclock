"""
led clock
a ntp synching clock in micropython
@author Russ Winch
@version December 2017
"""

import time
import network
import ntptime
from machine import Pin, SPI
from wifi import Wifi

def setTime():
    success_update = 300 # 5 mins
    fail_update = 10 # seconds
    last_update = time.time()
    try:
        ntptime.settime()
        update_interval = success_update
        print("succesfully synced time from ntp server: " + ntptime.host)
        print("next update in " + str(update_interval) + " seconds")
    except OSError:
        update_interval = fail_update
        print("error, couldn't retrieve time")
        print("trying again in " + str(update_interval) + " seconds")
    finally:
        return last_update, update_interval

# class DipSwitch:
#     '''controls dipswitches. not working yet but should enable easy addition'''
#     def __init__(self, switchPin):
#        self = Pin(switchPin, Pin.IN, Pin.PULL_UP)

    # def val(self):
    #     return 1 - self.Value()

class SevenSeg(object):
    """control of seven segment displays via MC14489B LED driver"""
    def __init__(self, csPin):
        # initialise spi
        self.spi = SPI(1, baudrate=5000000, polarity=0, phase=0)
        self.cs = Pin(csPin, Pin.OUT) # chip select
        self.cs.on()

    def writeOut(self, data):
        self.cs.off()
        self.spi.write(data)
        self.cs.on()

    def printSync(self):
        # displays the word 'sync'
        dreg = bytearray(3)
        dreg[0] = 0b10000000
        dreg[1] = 0b01011100
        dreg[2] = 0b01100001
        self.writeOut(dreg)

        creg = bytearray(1)
        creg[0] = 0b11001111
        self.writeOut(creg)

    def printConn(self):
        # displays the word 'Conn'
        dreg = bytearray(3)
        dreg[0] = 0b10000000
        dreg[1] = 0b11000111
        dreg[2] = 0b01100110
        self.writeOut(dreg)

        creg = bytearray(1)
        creg[0] = 0b11001111
        self.writeOut(creg)

    def printTime(self, h, m, s):
        print(time.localtime())
        # print(time.time())
        # print(ntptime.time())
        # if h > 12 and dip3.value() == 1:
        #     h -= 12 # 12 hour mode
        a = int(h / 10)
        b = h % 10
        c = int(m / 10)
        d = m % 10
        # if dip2.value() == 1:
        h = (s % 2) # flashing separator
        # else:
        #     h = 1 # static separator

        # data register
        dreg = bytearray(3)
        dreg[0] = 0b10000000 | h * 112 # if seconds are odd flash all decimals
        dreg[1] = (a << 4) + b # shift first nibble and add second to form a byte
        dreg[2] = (c << 4) + d
        self.writeOut(dreg)

        # control register
        creg = bytearray(1)
        creg[0] = 0b11000001 # first 2 bits define special decode option.
        if a == 0 and dip1.value() == 1:
            creg[0] |= 10000 # blank first digit with special decode
        self.writeOut(creg)

if __name__ == "__main__":
    display = SevenSeg(15) # init display with GPIO15 as the CS pin

    dip1 = Pin(5, Pin.IN, Pin.PULL_UP) # D1
    dip2 = Pin(4, Pin.IN, Pin.PULL_UP) # D2
    dip3 = Pin(16, Pin.IN) # D0

    # non working dipswitch class - to be continued
    # switchPins = [5,4]
    # dip = list()
    # for i in range(len(switchPins)):
    #     dip.append(DipSwitch(switchPins[i]))

    # connect to network
    display.printConn()
    wifi = Wifi()
    online = wifi.connect()

    if online:
        display.printSync()
        last_update, update_interval = setTime()
        # while setTime() == False:
        #     print('failed to set during initialise, 5 second retry')
        #     time.sleep(5)

        oldTime = time.time()

        while True:
            # check if an update is due
            if (time.time() - update_interval) > last_update:
                last_update, update_interval = setTime()

            # check if display needs updating
            if time.time() != oldTime:
                oldTime = time.time()
                display.printTime(time.localtime()[3], time.localtime()[4],
                        time.localtime()[5])
