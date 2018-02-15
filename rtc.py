"""RTC time control for DS1307.

Functionality to utilise the RTC over i2c

@version 14-Feb-2018
@author Russ Winch (github.com/russwinch)
"""

import time
from machine import I2C, Pin

# i2c = I2C(scl=Pin(2), sda=Pin(0), freq=100000)
i2c = I2C(scl=Pin(16), sda=Pin(0), freq=100000)

# mem = i2c.scan()
mem = 0x68
# print(mem[0])

def bcd2bin(value):
    return (value or 0) - 6 * ((value or 0) >> 4)

def bin2bcd(value):
    return (value or 0) + 6 * ((value or 0) // 10)

def start(mem):
    i2c.writeto_mem(mem, 0, b'0')

def read(mem):
    return i2c.readfrom_mem(mem, 0, 3)

def set(mem, newtime):
    buffer = bytearray(3)
    buffer[0] = bin2bcd(newtime[2])
    buffer[1] = bin2bcd(newtime[1])
    buffer[2] = bin2bcd(newtime[0])
    i2c.writeto_mem(mem, 0, buffer)

# start(mem[0])
set(mem, (22,20,00))

old_buffer = 0

while True:
    buffer = read(mem)
    if buffer != old_buffer:
            print("{h}:{m}:{s}".format(
            h=bcd2bin(buffer[2]), 
            m=bcd2bin(buffer[1]), 
            s=bcd2bin(buffer[0])))
            print('-------')
            old_buffer = buffer
    # time.sleep(1)
