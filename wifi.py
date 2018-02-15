"""
network functionality

@author Russ Winch
@version 1.0
"""

import network
import time
import json

class Wifi(object):

    def __init__(self):
        self.net = network.WLAN(network.STA_IF)

    def retrieve_credentials(self, filename="credentials.txt"):
        """
        collects wifi uid and password from text file
        file should be named 'credentials.txt'
        uid and password should be on separate lines:
        uid
        pass
        """
        try:
            with open(filename) as c:
                # uid = c.readline()
                # pasw = c.readline()
                # return {'uid': uid.strip(), 'pasw': pasw.strip()}
                return json.loads(c.read())
        except OSError as e:
            print("couldn't load credentials file")
            raise
            # return False

    def connect(self, timeout=15):
        # timeout = 15 # seconds

        if not self.net.isconnected():
            try:
                creds = self.retrieve_credentials()
            except:
            # if creds == False:
                print("failed due to no wifi credentials")
                raise
                # return False
            print("connecting to network:", creds['uid'])
            self.net.active(True)
            self.net.connect(creds['uid'], creds['pasw'])

            # set time to give up
            timeout += time.time()
            countdown = timeout - time.time()
            while not self.net.isconnected():
                if timeout != time.time():
                    # print when timeout changes, every second
                    if countdown != timeout - time.time():
                        countdown = timeout - time.time()
                        print("timeout in ", countdown, "seconds")
                else:
                    print("could't connect. timed out!")
                    # raise some timeout related exception here
                    return False
        print('connected!')
        print('ip config:', self.net.ifconfig())
        #no longer need to return True??h
        return True

#     def test_connected(self):
#         print(self.net.status())
#         print(self.net.ifconfig())
        # return self.net.isconnected()
