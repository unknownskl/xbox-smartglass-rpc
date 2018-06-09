# import time
#
# import os
# import logging
# import argparse
from gevent.pywsgi import WSGIServer

from api.router import HttpRouter
# from console.state import XboxState
#
# from xbox.sg.console import Console
# from xbox.sg.enum import DeviceStatus, ConnectionState, GamePadButton, MediaPlaybackStatus, MediaControlCommand
# from xbox.sg.manager import InputManager, TextManager, MediaManager
# from xbox.stump.manager import StumpManager

hostName = "0.0.0.0"
hostPort = 8000

version = '0.2.0'

def main():
    print('[ Xbox-RPC v%s] Starting...' % version)

    print('[ Xbox-RPC ] Serving webinterface on %s:%s' % (hostName, hostPort))
    WSGIServer(('', 8000), HttpRouter).serve_forever()

if __name__ == '__main__':
    main()
