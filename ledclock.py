"""
led clock.

An NTP synching clock in micropython
@author Russ Winch
@version January 2018 
"""

import time
import network
import ntptime
from machine import Pin, SPI
from wifi import Wifi


class DipSwitch:
    """controls dipswitches."""

    def __init__(self, switchPin):
        """initialise a dipswitch on the defined pin"""
        self.switch = Pin(switchPin, Pin.IN, Pin.PULL_UP)

    def value(self):
        return 1 - self.switch.value()


class SevenSeg(object):
    """control of seven segment displays via MC14489B LED driver"""

    def __init__(self, csPin):
        """initialise the SPI bus""" 
        self.spi = SPI(1, baudrate=5000000, polarity=0, phase=0)
        self.cs = Pin(csPin, Pin.OUT) # chip select
        self.cs.on()

    def writeOut(self, data):
        """sends data to the display over the SPI bus"""
        self.cs.off()
        self.spi.write(data)
        self.cs.on()

    def printSync(self):
        """displays the word 'Sync'"""
        dreg = bytearray(3)
        dreg[0] = 0b10000000
        dreg[1] = 0b01011100
        dreg[2] = 0b01100001
        self.writeOut(dreg)

        creg = bytearray(1)
        creg[0] = 0b11001111
        self.writeOut(creg)

    def printConn(self):
        """displays the word 'Conn'"""
        dreg = bytearray(3)
        dreg[0] = 0b10000000
        dreg[1] = 0b11000111
        dreg[2] = 0b01100110
        self.writeOut(dreg)

        creg = bytearray(1)
        creg[0] = 0b11001111
        self.writeOut(creg)

    def printTime(self, h, m, s, dips=None):
        """prints the time to the display"""
        print(time.localtime())

        for d, _ in enumerate(dips):
            print(dips[d].value())
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
        if a == 0: # and dip1.value() == 1:
            creg[0] |= 10000 # blank first digit with special decode
        self.writeOut(creg)


def setTime():
    """Retrieves the time from NTP server."""
    success_update = 300 # 5 mins
    fail_update = 10 # seconds
    last_update = time.time()

    try:
        ntptime.settime()
        update_interval = success_update
        print("succesfully synced time from ntp server: " + ntptime.host)
        print("next update in " + str(update_interval) + " seconds")
    except OSError as e:
        update_interval = fail_update
        print(e)
        print("error, couldn't retrieve time")
        print("trying again in " + str(update_interval) + " seconds")
    finally:
        return last_update, update_interval


def main():
    display = SevenSeg(15) # init display with GPIO15 as the CS pin

    # dip1 = Pin(5, Pin.IN, Pin.PULL_UP) # D1
    # dip2 = Pin(4, Pin.IN, Pin.PULL_UP) # D2
    # dip3 = Pin(16, Pin.IN) # D0

    switchPins = [5,4]
    dips = []
    for i, _ in enumerate(switchPins):
        dips.append(DipSwitch(switchPins[i]))

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
                display.printTime(
                        h = time.localtime()[3],
                        m = time.localtime()[4],
                        s = time.localtime()[5],
                        dips = dips)


if __name__ == "__main__":
    main()
