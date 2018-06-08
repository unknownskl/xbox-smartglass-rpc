import os
from xbox.sg.console import Console
from console.state import XboxState

class Xbox:
    def __init__(self, console = False):
        self._console = console

        if console != False:
            self.state = XboxState()

    def to_json(self):
        return {
            'name': self._console.name,
            'address': self._console.address,
            # 'uuid': self._console.uuid,
            'liveid': self._console.liveid,
            # 'flags': self._console.flags,
            #'public_key': self._console.public_key,
        }

    def discover(self = False):
        print('[console/xbox.py: Xbox.discover] Starting discovery...')
        consoles = Console.discover(addr = os.environ['XBOX_IP']);
        found = {}
        for console in consoles:
            xbox_console = Xbox(console)
            print('[console/xbox.py: Xbox.discover] Xbox found: %s' % (xbox_console.to_json()))
            found[console.name] = xbox_console

        return found
