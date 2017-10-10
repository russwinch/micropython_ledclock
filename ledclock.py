import network
import time
import ntptime
import machine

def wifi_connect():
    sta_if = network.WLAN(network.STA_IF)
    try:
        with open("credentials.txt") as c:
            uid = c.readline()
            pasw = c.readline()
    except OSError:
        print('couldn\'t load credentials file')
    if not sta_if.isconnected():
        timeout = time.time() + 10 #seconds
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

def displayTime(h, m, s):
    print(time.localtime())
    a = int(h / 10)
    b = h % 10
    c = int(m / 10)
    d = m % 10
    h = (s % 2) * 112

    # data register
    dreg = bytearray(3)
    dreg[0] = 0b10000000 | h # if seconds are odd flash all decimals
    dreg[1] = (a << 4) + b # shift first nibble and add second to form a byte
    dreg[2] = (c << 4) + d
    writeOut(dreg)

    # control register
    creg = bytearray(1)
    creg[0] = 0b11000001 # first 2 bits define special decode option.
    if a == 0:
        creg[0] |= 10000 # blank first digit with special decode
    writeOut(creg)

# displays the word 'sync'
def displaySync():
    dreg = bytearray(3)
    dreg[0] = 0b10000000
    dreg[1] = 0b01011100
    dreg[2] = 0b01100001
    writeOut(dreg)

    creg = bytearray(1)
    creg[0] = 0b11001111
    writeOut(creg)

def writeOut(self):
    cs.off()
    spi.write(self)
    cs.on()

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

# initialise spi
spi = machine.SPI(1, baudrate=5000000, polarity=0, phase=0)
cs = machine.Pin(15, machine.Pin.OUT) # chip select
cs.on()

# connect to network
wifi_connect() #** add retry functionality**
while setTime() == False:
    displaySync()
oldTime = time.time()

while True:
    # if checkUpdate(LASTUPDATE, UPDATEINTERVAL) == True:
    if time.time() - (UPDATEINTERVAL) > LASTUPDATE:
        setTime()

    if time.time() != oldTime:
        oldTime = time.time()
        displayTime(time.localtime()[3]+1, time.localtime()[4],
                time.localtime()[5]) #BST hack for hour!
