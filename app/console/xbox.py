import os
from xbox.sg.console import Console
from xbox.sg.enum import DeviceStatus, ConnectionState, GamePadButton, MediaPlaybackStatus, MediaControlCommand
from xbox.sg.manager import InputManager, TextManager, MediaManager
from xbox.stump.manager import StumpManager

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
            'state': self.state.to_json()
        }

    def getName(self):
        return self._console.name

    def discover(self = False):
        print('[Xbox.discover] Starting discovery...')
        consoles = Console.discover(addr = os.environ['XBOX_IP']);
        found = {}
        for console in consoles:
            xbox_console = Xbox(console)
            print('[Xbox.discover] Xbox found: %s' % (xbox_console.to_json()))
            found[console.name] = xbox_console

        return found

    def connect(self):
        print("[Xbox.connect] Opening connection to Xbox")
        print("[Xbox.connect] Activated MediaManager (beta)")
        self._console.add_manager(MediaManager)

        print("[Xbox.connect] Activated StumpManager (beta)")
        self._console.add_manager(StumpManager)

        self._console.on_connection_state += lambda _: self._on_refresh_connection()
        self._console.on_console_status += lambda _: self._on_refresh_status()

        state = self._console.connect()

        if state == ConnectionState.Connected:
            print("[Xbox.connect] Xbox Connected")
            self.state.setConnected(True)
            return True
        else:
            print("[Xbox.connect] Failed to connect to Xbox")
            self.state.setConnected(False)
            return False

    def _on_refresh_status(self):
        print("[Xbox._on_refresh_status] Got status update from Xbox: %s" % self.getName())
        self.state.setTitles(self._console.console_status.get('active_titles'))

    def _on_refresh_connection(self):
        if self._console.connection_state == ConnectionState.Connected:
            print("[Xbox._on_refresh_connection] State is: connected")
            self.state.setConnected(True)
        else:
            print("[Xbox._on_refresh_connection] State is: disconnected")
            self.state.setConnected(False)
