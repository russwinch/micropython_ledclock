"""
led clock.

An NTP synching clock in micropython
@author Russ Winch
@version January 2018 
"""

import time
# import network
import ntptime
from machine import Pin, SPI
from wifi import Wifi


class DipSwitch(object):
    """
    controls dipswitches.
    improve this by passing in the pull up option.
    """

    def __init__(self, switchPin):
        """initialise a dipswitch on the defined pin"""
        self.switch = Pin(switchPin, Pin.IN, Pin.PULL_UP)

    def value(self):
        """returns the inverted dipswitch value. due to the pull up"""
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
        print("----------")
        print("{hrs}:{mins}:{secs}".format(hrs=h, mins=m, secs=s))

        if dips:
            for d, _ in enumerate(dips):
                print("dipswitch {d}: {val}".format(d=d, val=dips[d].value()))

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
        dreg[1] = (a << 4) + b # shift first nibble and add second
        dreg[2] = (c << 4) + d
        self.writeOut(dreg)

        # control register
        creg = bytearray(1)
        creg[0] = 0b11000001 # first 2 bits define special decode option.
        if a == 0  and dips[1].value() == 1:
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
        print("next update in {} seconds".format(update_interval))
    except OSError as e:
        update_interval = fail_update
        print(e)
        print("error, couldn't retrieve time")
        print("trying again in {} seconds".format(update_interval))
    finally:
        return last_update, update_interval


# function to set RTC

# function to convert from DEC to BCD

# function to convert from BCD to DEC

# function to retrieve the time from the RTC

# function to log the retrieved data and any errors from the retreived time
#load this from external file...

def main():
    display = SevenSeg(15) # init display with GPIO15 as the CS pin

    switchPins = [5,4] # D1, D2
    dips = []
    for i, _ in enumerate(switchPins):
        dips.append(DipSwitch(switchPins[i]))

    # connect to network
    display.printConn()
    wifi = Wifi()
    online = False
    while not online:
        online = wifi.connect()

    display.printSync()
    # issue here needs resolving as failure to retrive time results in 00:00
    last_update, update_interval = setTime()
    oldTime = time.time()

    while True:
        # check if an update is due
        if (time.time() - update_interval) > last_update:
            last_update, update_interval = setTime()

        # check if display needs updating
        if time.time() != oldTime:
            oldTime = time.time()
            # print(time.localtime())
            display.printTime(
                    h = time.localtime()[3],
                    m = time.localtime()[4],
                    s = time.localtime()[5],
                    dips = dips)


if __name__ == "__main__":
    main()
