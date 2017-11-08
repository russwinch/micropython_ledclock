"""
led clock
a ntp synching clock in micropython
@author Russ Winch
@version October 2017
"""

import time
import network
import ntptime
from machine import Pin, SPI

def wifi_connect():
    """
    connects to wifi
    """
    sta_if = network.WLAN(network.STA_IF)
    try:
        with open("credentials.txt") as c:
            uid = c.readline()
            pasw = c.readline()
    except OSError:
        print('couldn\'t load credentials file')
    if not sta_if.isconnected():
        timeout = time.time() + 20 #seconds
        print('connecting to network:', uid)
        sta_if.active(True)
        sta_if.connect(uid.strip(), pasw.strip()) # strip newlines
        while not sta_if.isconnected():
            countdown = timeout - time.time()
            if countdown > 0:
                print('timeout in ', countdown, 'seconds')
                time.sleep(1)
            else:
                print('could\'t connect. timed out!')
                return False
        print('connected!')
        print('ip config:', sta_if.ifconfig())
        return True

class Wifi(object):
    """
    network functionality
    """

    # import network # required here?
    timeout = 10 # seconds
    
    def __init__(self):
        self.net = network.WLAN(network.STA_IF)

    def retrieve_credentials(self):
        try:
            with open("credentials.txt") as c:
                uid = c.readline()
                pasw = c.readline()
                return {'uid': uid.strip(), 'pasw': pasw.strip()}
        except OSError:
            print('couldn\'t load credentials file')
            return False

    def connect(self):
        if not self.net.isconnected():
            creds = self.retrieve_credentials() # cant currently handle failure
            timeout = time.time() + 20 #seconds
            print('connecting to network:', creds['uid'])
            self.net.active(True)
            self.net.connect(creds['uid'], creds['pasw'])
            while not self.net.isconnected():
                countdown = timeout - time.time()
                if countdown > 0:
                    print('timeout in ', countdown, 'seconds')
                    time.sleep(1)
                else:
                    print('could\'t connect. timed out!')
                    return False
            print('connected!')
            print('ip config:', self.net.ifconfig())
            return True

    def test_connected(self):
        print(self.net.status())
        print(self.net.ifconfig())
        return self.net.isconnected()

def setTime():
    global LASTUPDATE
    global UPDATEINTERVAL
    LASTUPDATE = time.time()
    try:
        ntptime.settime()
        UPDATEINTERVAL = 300 #5mins
        print('succesfully synced time from ntp server: ' + ntptime.host)
        print('next update in ' + str(UPDATEINTERVAL) + ' seconds')
        return True
    except OSError:
        UPDATEINTERVAL = 10 #seconds
        print('error, couldn\'t retrieve time')
        print('trying again in ' + str(UPDATEINTERVAL) + ' seconds')
        return False

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
    wifi.connect()

    # wifi_connect() #** add retry functionality**
    display.printSync()
    while setTime() == False:
        print('failed to set during initialise, 5 second retry')
        time.sleep(5)
    oldTime = time.time()

    while True:
        if time.time() - (UPDATEINTERVAL) > LASTUPDATE:
            setTime()

        if time.time() != oldTime:
            oldTime = time.time()
            display.printTime(time.localtime()[3], time.localtime()[4],
                    time.localtime()[5])
