"""
led clock.

An NTP synching clock in micropython
@author Russ Winch
@version 2.1 - February 2018 
"""

import time
import ntptime
from machine import I2C, Pin, SPI
from ucollections import namedtuple
from rtc import RTC
from wifi import Wifi

OptionsTuple = namedtuple("OptionsTuple", [
                                "daylight_saving",
                                "flash_separator",
                                "leading_zero",
                                "twelve_hour_mode"])

class DipSwitch(object):
    """Controls dipswitches."""

    def __init__(self, switch_pin):
        """initialise a dipswitch on the defined pin"""
        self.switch = Pin(switch_pin, Pin.IN, Pin.PULL_UP)

    def value(self):
        """returns the inverted dipswitch value, due to the pull up"""
        return 1 - self.switch.value()


class SevenSeg(object):
    """Control of seven segment displays via MC14489B LED driver."""

    def __init__(self, chip_select_pin, spi):
        """initialise the SPI bus""" 
        self.spi = spi
        self.cs = Pin(chip_select_pin, Pin.OUT) # chip select
        self.cs.on()

    def write_out(self, data):
        """sends data to the display over the SPI bus"""
        self.cs.off()
        self.spi.write(data)
        self.cs.on()

    def print_sync(self):
        """displays the word 'Sync'"""
        dreg = bytearray(3)
        dreg[0] = 0b10000000
        dreg[1] = 0b01011100
        dreg[2] = 0b01100001
        self.write_out(dreg)

        creg = bytearray(1)
        creg[0] = 0b11001111
        self.write_out(creg)

    def print_conn(self):
        """displays the word 'Conn'"""
        dreg = bytearray(3)
        dreg[0] = 0b10000000
        dreg[1] = 0b11000111
        dreg[2] = 0b01100110
        self.write_out(dreg)

        creg = bytearray(1)
        creg[0] = 0b11001111
        self.write_out(creg)

    def print_time(
            self,
            hour,
            minute,
            second,
            leading_zero=False,
            flash_separator=True):
        """prints the time to the display"""
        print("{h}:{m}:{s}".format(h=hour, m=minute, s=second))
        print("----------")

        # break digits down into led banks
        bank_a = int(hour / 10)
        bank_b = hour % 10
        bank_c = int(minute / 10)
        bank_d = minute % 10
        if flash_separator:
            bank_h = (second % 2) # flashing separator
        else:
            bank_h = 1 # static separator

        # data register
        dreg = bytearray(3)
        dreg[0] = 0b10000000 | bank_h * 112 # when seconds odd flash decimals
        dreg[1] = (bank_a << 4) + bank_b # shift first nibble and add second
        dreg[2] = (bank_c << 4) + bank_d # shift first nibble and add second
        self.write_out(dreg)

        # control register
        creg = bytearray(1)
        creg[0] = 0b11000001 # first 2 bits define special decode option.
        if bank_a == 0 and not leading_zero:
            creg[0] |= 10000 # blank first digit with special decode
        self.write_out(creg)


def retrieve_ntp_time():
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


def dst(hour, apply_dst, time_diff):
    """Applies time difference to hours if apply_dst is True"""
    if apply_dst:
        hour += time_diff
        if hour > 23:
            hour -= 24 
    return hour


def hour_mode(hour, apply_12hr):
    """Applies 12 hour mode if apply_12hr is True, else 24 hour mode."""
    if apply_12hr:
        if hour > 12:
            hour -= 12
    return hour


def get_options(options):
    """Retrieves the latest options from dipswitches or returns bools."""
    latest_options = []
    for o,_ in enumerate(options):
        if type(options[o]) == bool:
            latest_options.append(options[o])
        else:
            latest_options.append(options[o]())
    return OptionsTuple(*latest_options)


# function to log the retrieved data and any errors from the retreived time
#load this from external file...

def main():
    # initialise spi bus and i2c bus
    spi = SPI(1, baudrate=5000000, polarity=0, phase=0)
    i2c = I2C(scl=Pin(16), sda=Pin(0), freq=100000) # scl=D0 sda=D3

    display = SevenSeg(15, spi) # init display with CS pin GPIO15 D8 on spi 
    rtc = RTC(i2c) # init rtc on i2c bus

    # create dipswitches
    switchPins = [5,4] # D1, D2
    dips = []
    for i, _ in enumerate(switchPins):
        dips.append(DipSwitch(switchPins[i]))

    # settings for the clock
    options = OptionsTuple(
                daylight_saving = dips[0].value,
                flash_separator = True,
                leading_zero = True,
                twelve_hour_mode = dips[1].value)

    # connect to network
    display.print_conn()
    wifi = Wifi()
    online = False
    while not online:
        online = wifi.connect()

    display.print_sync()
    # issue here needs resolving as failure to retrive time results in 00:00
    last_update, update_interval = retrieve_ntp_time()
    rtc.set_time(time.localtime()[3:6])
    old_time = rtc.get_time() 

    while True:
        # check if an update is due
        if (time.time() - update_interval) > last_update:
            # add check for online here
            last_update, update_interval = retrieve_ntp_time()
            rtc.set_time(time.localtime()[3:6])

        rtc_time = rtc.get_time()
        # check if display needs updating
        if rtc_time != old_time:
            old_time = rtc_time
            retrieved_options = get_options(options)
            print(retrieved_options)
            display.print_time(
                        hour=hour_mode(
                            hour=dst(
                                hour=rtc_time.hour,
                                apply_dst=retrieved_options.daylight_saving,
                                time_diff=1),
                            apply_12hr=retrieved_options.twelve_hour_mode),
                        minute=rtc_time.minute,
                        second=rtc_time.second,
                        leading_zero=retrieved_options.leading_zero,
                        flash_separator=retrieved_options.flash_separator)

if __name__ == "__main__":
    main()
