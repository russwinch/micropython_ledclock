"""
Lightweight logging.

Functionality to write to a specified file, 
clear the file, count the lines in the file.
"""

class Logs(object):

    def __init__(self, filename='logs.txt'):
        """Initialise the object with a default filename, unless specified."""
        self.filename = filename

    def clear_file(self):
        """Clear down the file. Useful if it is getting too big."""
        with open(self.filename, mode='w'):
            pass
        print("Log file {} cleared.".format(self.filename))

    def log(self, data):
        """write a new line of logging data to the file."""
        with open(self.filename, mode='a') as f:
            f.write(str(data) + '\n')

    def count_lines(self):
        """Return the total lines currently in the file."""
        total_lines = 0
        try:
            with open(self.filename) as f:
                while f.readline():
                    total_lines += 1
        except FileNotFoundError as e:
            print("File doesn't exist: {}".format(e))
        return total_lines
