import os
import time
from xbox.sg.console import Console
from xbox.sg.enum import DeviceStatus, ConnectionState, GamePadButton, MediaPlaybackStatus, MediaControlCommand
from xbox.sg.manager import InputManager, TextManager, MediaManager
from xbox.stump.manager import StumpManager

from console.state import XboxState
from api.cache import ApiCache

class Xbox:
    def __init__(self, console = False):
        self._console = console

        if console != False:
            self.state = XboxState(console)

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
        self._console.media.on_media_state += lambda _: self._on_refresh_media()

        state = self._console.connect()

        if state == ConnectionState.Connected:
            print("[Xbox.connect] Xbox Connected")
            self.state.setConnected(True)
            return True
        else:
            print("[Xbox.connect] Failed to connect to Xbox")
            self.state.setConnected(False)
            return False

    def power_off(self):
        if self.state.isConnected() == True:
            print("[Xbox.power_off] Turning off Xbox: %s" % self.getName())
            self._console.power_off()
            return True
        else:
            return False

    def power_on(liveId, tries = 5):
        print("[Xbox.power_on] Booting Xbox with liveID: %s (%s)" % (liveId, os.environ['XBOX_IP']))
        for num in range(1, tries):
            Console.power_on(liveId, os.environ['XBOX_IP'], tries=20)
            print('[Xbox.power_on] Broadcasting packet (%s/%s)' % (num, tries))

        consoles = Xbox.discover()
        for console in consoles:
            if consoles[console]._console.liveid == liveId:
                return consoles[console]

        return False

    def launch_uri(self, uri):
        if self.state.isConnected() == True:
            self._console.launch_title(uri)
            return True
        else:
            return False

    def get_ir_configuration(self):
        if self.state.isConnected() == True:
            configuration = self._console.request_stump_configuration()

            return configuration
        else:
            return False

    def _on_refresh_status(self):
        print("[Xbox._on_refresh_status] Got status update from Xbox: %s" % self.getName())
        self.state.setTitles(self._console.console_status.get('active_titles'))

    def _on_refresh_media(self):
        print("[Xbox._on_refresh_media] Got status update from Xbox: %s" % self.getName())
        print("[Xbox._on_refresh_media] @TODO: Implement this function")
        print(self._console.media_state)

    def _on_refresh_connection(self):
        if self._console.connection_state == ConnectionState.Connected:
            print("[Xbox._on_refresh_connection] State is: connected")
            self.state.setConnected(True)
            ApiCache._activeConnections[self._console.liveid] = False
        else:
            print("[Xbox._on_refresh_connection] State is: disconnected")
            self.state.setConnected(False)
            if self._console.liveid in ApiCache._activeConnections:
                del ApiCache._activeConnections[self._console.liveid]
