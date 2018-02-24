"""RTC time control for DS1307.

Utilise the time functionality of the RTC over i2c.
This only includes the hours, minutes and seconds. 
Based on the uRTC module from Adafruit
https://github.com/adafruit/Adafruit-uRTC

@version 0.2 - February 2018
@author Russ Winch (github.com/russwinch)
"""

# import time # for testing only
# import ucollections
from ucollections import namedtuple
# from machine import I2C, Pin # for testing only

# for testing only, move our of here and pass in these variables
# i2c = I2C(scl=Pin(16), sda=Pin(0), freq=100000)
# address = 0x68

TimeTuple = namedtuple("TimeTuple", ["hour", "minute", "second"])

def timetuple(hour=0, minute=0, second=0):
    """creates a TimeTuple named tuple object"""
    return TimeTuple(hour, minute, second)

def bcd2bin(value):
    """Converts from Binary Coded Decimal"""
    return (value or 0) - 6 * ((value or 0) >> 4)

def bin2bcd(value):
    """Converts to Binary Coded Decimal"""
    return (value or 0) + 6 * ((value or 0) // 10)


class RTC(object):

    def __init__(self, i2c, address=0x68):
        """Initialise with the i2c object and optionally the i2c address"""
        self.i2c = i2c
        self.address = address

    def start_clock(self):
        """Start the clock by resetting the seconds to zero, for testing"""
        buffer = bytearray(1)
        buffer[0] = 0
        self.i2c.writeto_mem(self.address, 0, buffer)

    def get_time(self):
        """Retrieve 3 bytes of time from the RTC and return as a timetuple"""
        buffer =  self.i2c.readfrom_mem(self.address, 0, 3)
        return timetuple(
                hour=bcd2bin(buffer[2]),
                minute=bcd2bin(buffer[1]),
                second=bcd2bin(buffer[0]))

    def set_time(self, newtime):
        """Write 3 bytes of time to the RTC"""
        newtime = timetuple(*newtime)
        buffer = bytearray(3)
        buffer[0] = bin2bcd(newtime.second)
        buffer[1] = bin2bcd(newtime.minute)
        buffer[2] = bin2bcd(newtime.hour)
        # buffer[0] = bin2bcd(newtime[2])
        # buffer[1] = bin2bcd(newtime[1])
        # buffer[2] = bin2bcd(newtime[0])
        self.i2c.writeto_mem(self.address, 0, buffer)

if __name__ == "__main__":
    # start(address)
    # set(address, (8,17,37))

    # old_buffer = 0
    rtc = RTC(i2c)
    new_time = timetuple(hour=21, minute=5, second=35)
    rtc.set_time(new_time)
    # rtc.set_time((22, 30, 45))

    while True:
        # buffer = read(address)
        # if buffer != old_buffer:
        #         print("{h}:{m}:{s}".format(
        #         h=bcd2bin(buffer[2]), 
        #         m=bcd2bin(buffer[1]), 
        #         s=bcd2bin(buffer[0])))
        #         print('-------')
        #         old_buffer = buffer
        print(rtc.get_time())
        time.sleep(1)
