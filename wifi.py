"""
network functionality

@author Russ Winch
@version 1.0
"""

import network
import time

class Wifi(object):

    def __init__(self):
        self.net = network.WLAN(network.STA_IF)

    def retrieve_credentials(self):
        """
        collects wifi uid and password from text file
        file should be named 'credentials.txt'
        uid and password should be on separate lines:
        uid
        pass
        """
        try:
            with open("credentials.txt") as c:
                uid = c.readline()
                pasw = c.readline()
                return {'uid': uid.strip(), 'pasw': pasw.strip()}
        except OSError:
            print("couldn't load credentials file")
            return False

    def connect(self):
        timeout = 15 # seconds

        if not self.net.isconnected():
            creds = self.retrieve_credentials()
            if creds == False:
                print("failed due to no wifi credentials")
                return False
            print("connecting to network:", creds["uid"])
            self.net.active(True)
            self.net.connect(creds['uid'], creds['pasw'])
            timeout += time.time()
            countdown = timeout - time.time()
            while not self.net.isconnected():
                if timeout != time.time():
                    if countdown != timeout - time.time():
                        countdown = timeout - time.time()
                        print("timeout in ", countdown, "seconds")
                else:
                    print("could't connect. timed out!")
                    return False
        print('connected!')
        print('ip config:', self.net.ifconfig())
        return True

    def test_connected(self):
        print(self.net.status())
        print(self.net.ifconfig())
        return self.net.isconnected()
