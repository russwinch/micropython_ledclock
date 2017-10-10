import network
import time
import ntptime
import machine

def wifi_connect():
    sta_if = network.WLAN(network.STA_IF)
    try:
        with open("credentials.txt") as c:
            u = c.readline()
            p = c.readline()
    except OSError:
        print('couldn\'t load credentials file')
    if not sta_if.isconnected():
        timeout = time.time() + 10 #seconds
        print('connecting to network:', u)
        sta_if.active(True)
        sta_if.connect(u.strip(), p.strip()) # strip newlines
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

def display(a,b,c,d,h):
    # data register
    dreg = bytearray(3)
    dreg[0] = 0b10000000 | (h << 4) # if seconds are odd flash bank1 decimal
    dreg[1] = (a << 4) + b # shift first nibble and add second to form a byte
    dreg[2] = (c << 4) + d
    cs.off()
    spi.write(dreg)
    cs.on()

    # control register
    creg = bytearray(1)
    creg[0] = 0b11000001 # first 2 bits define special decode option.
    if a == 0:
        creg[0] |= 10000 # blank first digit with special decode
    cs.off()
    spi.write(creg)
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
        # return True
    except OSError:
        UPDATEINTERVAL = 10 #seconds
        print('error, couldn\'t retrieve time')
        print('trying again in ' + str(UPDATEINTERVAL) + ' seconds')
        # return False

def checkUpdate(last, interv):
    if time.time() - (interv) > last:
        return True
    else:
        return False

def printTime(h, m, s):
    print(time.localtime())
    h1 = int(h/10)
    h2 = h%10
    m1 = int(m/10)
    m2 = m%10
    s1 = s%2
    display(h1,h2,m1,m2,s1)

# initialise spi
spi = machine.SPI(1, baudrate=5000000, polarity=0, phase=0)
cs = machine.Pin(15, machine.Pin.OUT) # chip select
cs.on()

# connect to network
wifi_connect() #** add retry functionality**
setTime()
oldTime = time.time()

while True:
    if checkUpdate(LASTUPDATE, UPDATEINTERVAL) == True:
        setTime()

    if time.time() != oldTime:
        oldTime = time.time()
        printTime(time.localtime()[3]+1, time.localtime()[4],
                time.localtime()[5]) #BST hack for hour!
