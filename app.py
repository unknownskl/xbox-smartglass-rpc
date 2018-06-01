import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

import json
import os

from xbox.sg.console import Console
from xbox.sg.enum import DeviceStatus, ConnectionState, GamePadButton, MediaPlaybackStatus
from xbox.sg.manager import InputManager, TextManager, MediaManager

hostName = "0.0.0.0"
hostPort = 8000

class Xbox:
    def __init__(self):
        self.console = False
        self.console_data = False
        self.request_id = 0

    def findDevice(self, tries = 1):
        print("[Xbox.findDevice] called (Try #%d)" % tries)
        console = self.discovery(timeout = 5, addr = os.environ['XBOX_IP'])
        if tries == 3:
            print("[Xbox.findDevice] Max tries reached. No consoles found")
            return False

        if isinstance(console, Console):
            self.console_data = {
                "address": console.address,
                "name": console.name,
                "uuid": console.uuid,
                "liveid": console.liveid,
                "flags": console.flags,
                "public_key": console.public_key,
            }
        else:
            self.console_data = self.findDevice(tries = tries+1)

        return self.console_data

    def fetchMediaStatus(self, tries = 1):

        print("[Xbox.fetchMediaStatus] called (Try #%d)" % tries)
        if tries == 5:
            return False

        if self.console.title_id == None:
            self.console.protocol.serve_forever()
            return self.fetchMediaStatus(tries = tries+1)
        else:
            return self.console.media_state

    def onMediaState(self, state):
        print(state)
        print("[Xbox.onMediaState] called (State: %s)" % state)
        self.console.protocol.shutdown()
        return

    def getInstance(self, mode = 'default', connect = True):

        print("[Xbox.getInstance] called (mode: %s, connect: %s)" % (mode, connect))

        if self.console_data == False:
            data = self.findDevice()
            if data == False:
                print("[Xbox.getInstance] Result of self.findDevice() = %s" % data)
                return False

        self.console = Console(
            address = self.console_data.get("address"),
            name = self.console_data.get("name"),
            uuid = self.console_data.get("uuid"),
            liveid = self.console_data.get("liveid"),
            flags = self.console_data.get("flags"),
            public_key = self.console_data.get("public_key"),
        )

        if mode == 'media':
            print("[Xbox.getInstance] Activated MediaManager")
            self.console.add_manager(MediaManager)
            self.console.media.on_media_state += self.onMediaState

        if connect == False:
            return self.console
        else:
            print("[Xbox.getInstance] Connecting to Xbox")
            self.console.connect()

            if self.console.connection_state == ConnectionState.Connected:
                print("[Xbox.getInstance] Xbox Connected")
                self.console.wait(0.5)
                connected = True
            else:
                print("[Xbox.getInstance] [ERROR] Could not connect to Xbox")
                conected = False

            if connected == True:
                return self.console
            else:
                return False

    def discovery(self, timeout, addr):
        return self.do_discovery(addr = addr, tries = timeout)

    def do_discovery(self, addr, tries):
        consoles = Console.discover(addr = addr, tries = tries);
        print("[Xbox.do_discovery] Consoles found:")
        print(consoles)
        if len(consoles) > 0:
            print("[Xbox.do_discovery] Console found")
            return consoles[0]
        else:
            print("[Xbox.do_discovery] No consoles found")
            return False

    def media_command(self, media_command):
        print("[Xbox.media_command] called (media_command: %s)" % media_command)
        action = self.console.media_command(0x54321, media_command, self.request_id)
        return action

    def power_on(self):

        if os.environ['XBOX_IP'] != "127.0.0.1":
            print("[Xbox.power_on] Booting xbox from config settings (%s, %s)" % (os.environ['XBOX_IP'], os.environ['XBOX_LIVEID']))
            Console.power_on(os.environ['XBOX_LIVEID'], os.environ['XBOX_IP'], tries=20)
            data = True

        else:
            console = self.getInstance(connect = False);
            if console != False:
                print("[Xbox.power_on] Booting xbox from discovery settings(%s, %s)" % (self.console_data.get("address"), self.console.get("liveid")))
                Console.power_on(self.console_data.get("liveid"), self.console.get("address"), tries=20)
                data = True
            else:
                data = ['No device found in cache. Turn on your xbox and run /api/v1/discovery']

        return data

    def power_off(self):
        self.console.power_off()
        self.console.wait(1)
        return True

    def close(self):
        print("[Xbox.close] called ()")
        self.console.disconnect()
        self.console = False
        return True

    def connect(timeout):
        discovered = Console.discover(timeout=1);
        if len(discovered):
            return discovered[0]
        return discovered

class MyServer(BaseHTTPRequestHandler):

    def do_GET(self):
        print("[Http.Get] %s called" % self.path)

        if self.path == "/api/v1/discovery":
            console = Xbox.findDevice()
            consolesFound = []

            if console != False:
                consoleData = {
                    "name": console.get("name"),
                    "address": console.get("address"),
                    "liveid": console.get("liveid"),
                }
                consolesFound.append(consoleData)

            self.sendResponse(consolesFound)

        elif self.path == "/api/v1/poweroff":
            console = Xbox.getInstance();
            data = Xbox.power_off()

            if data == True:
                self.sendResponse({
                    'success': True
                })
            else:
                self.sendResponse(data)
            Xbox.close()

        elif self.path == "/api/v1/poweron":
            data = Xbox.power_on()
            if data == True:
                self.sendResponse({
                    'success': True
                })
            else:
                self.sendResponse(data)

        elif self.path == "/api/v1/status":
            console = Xbox.getInstance();
            print(console)
            if console != False:
                print("[Http.Get] Returning online console status")
                status = console.console_status()

                mediaMode = None
                mediaApplication = None

                activeTitles = []
                for Title in status.active_titles:
                    titleStruct = {
                        'title_id': Title.title_id,
                        'focus': Title.disposition.has_focus,
                        'uam_id': Title.aum,
                    }

                    type = Title.aum.split('!')[1]
                    name = Title.aum.split('!')[0]

                    if type == 'App':
                        if name == '4DF9E0F8.Netflix_mcm4njqhnhss8':
                            mediaMode = "video"
                            mediaApplication = "netflix"

                        elif name == 'XBMCFoundation.Kodi_4n2hpmxwrvr6p':
                            mediaMode = "video"
                            mediaApplication = "kodi"

                        elif name == 'SpotifyAB.SpotifyMusic-forXbox_zpdnekdrzrea0':
                            mediaMode = "audio"
                            mediaApplication = "spotify"

                        elif name == 'SpotifyAB.SpotifyMusic-forXbox_zpdnekdrzrea0':
                            mediaMode = "audio"
                            mediaApplication = "spotify"

                        else:
                            mediaApplication = name
                            mediaMode = "app"

                    elif type == 'Microsoft.Xbox.LiveTV.Application':
                        mediaMode = "tv"
                        mediaApplication = "livetv"

                    elif type == 'Xbox.Dashboard.Application':
                        mediaMode = "standby"
                        mediaApplication = "dashboard"

                    elif type == 'Xbox.Settings.Application':
                        mediaMode = "standby"
                        mediaApplication = "settings"

                    else:
                        mediaMode = "game"
                        mediaApplication = name

                    activeTitles.append(titleStruct)

                print("[Http.Get] active_tiles: %s" % activeTitles )
                print("[Http.Get] mode: %s" % mediaMode )
                print("[Http.Get] application: %s" % mediaApplication )
                print("[Http.Get] build_number: %s" % status.build_number )
                data = {
                    'status': 'online',
                    'build_number': status.build_number,
                    'active': activeTitles,
                    'mode': mediaMode,
                    'application': mediaApplication
                }
                Xbox.close()
            else:
                print("[Http.Get] Returning offline console status")
                data = {
                    'status': 'offline',
                    'build_number': False,
                    'active': [],
                    'mode': 'off',
                    'application': 'none'
                }

            self.sendResponse(data)

        elif self.path[:15] == "/api/v1/launch/":
            console = Xbox.getInstance(mode = 'media');
            appId = self.path[15:]

            if console != False:
                status = console.launch_title(appId)

                print(status)

                data = {
                    'status': 'ok',
                }
                Xbox.close()
            else:
                data = {
                    'status': 'error'
                }

            self.sendResponse(data)

        # Disabled due not working
        # elif self.path[:19] == "/api/v1/mediastatus":
        #     console = Xbox.getInstance(mode = 'media');
        #     if console != False:
        #
        #         mediastatus = Xbox.fetchMediaStatus()
        #         print(mediastatus)
        #
        #         #if console.media_state == None
        #         #print(console)
        #
        #         data = {
        #             'status': 'ok',
        #         }
        #     else:
        #         data = {
        #             'status': 'error'
        #         }
        #
        #     self.sendResponse(data)
        #     Xbox.close()

        elif self.path[:13] == "/api/v1/media":
            action = self.path[14:]

            possibleActions = {
                "play": MediaControlCommand.Play,
                "pause": MediaControlCommand.Pause,
                "stop": MediaControlCommand.Stop,
                "playpause": MediaControlCommand.PlayPauseToggle,
                "record": MediaControlCommand.Record,
                "next": MediaControlCommand.NextTrack,
                "previous": MediaControlCommand.PreviousTrack,
                "channelup": MediaControlCommand.ChannelUp,
                "channeldown": MediaControlCommand.ChannelDown,
            }

            if action in possibleActions:
                console = Xbox.getInstance(mode = 'media');
                if console != False:
                    action = Xbox.media_command(media_command = possibleActions.get(action))
                    data = {
                        'status': 'ok',
                    }
                else:
                    data = {
                        'status': 'error'
                    }

                self.sendResponse(data)
                Xbox.close()
            elif action == '':
                data = []
                for action in possibleActions.keys():
                    data.append("/api/v1/media/%s" % action)

                self.sendResponse(data)
            else:
                self.sendResponse('Action not found', 404)

        elif self.path == "/api/v1/data":
            console = Xbox.getInstance(connect = False);
            consolesFound = []

            if console != False:
                consoleData = {
                    "name": console.name,
                    "address": console.address,
                    "liveid": console.liveid,
                }
                consolesFound.append(consoleData)

            data = {
                'consoles_found': consolesFound,
                'console_data': {
                    "name": Xbox.console_data.get("name"),
                    "address": Xbox.console_data.get("address"),
                    "liveid": Xbox.console_data.get("liveid"),
                }
            }
            self.sendResponse(data)
        elif self.path == "/api/v1/switch":
            console = Xbox.getInstance();
            if console == False:
                data = { 'status': False }
            else:
                data = { 'status': True }
                Xbox.close()

            self.sendResponse(data)
        elif self.path == "/":
            data = [
                "/api/v1/discovery",

                "/api/v1/poweron",
                "/api/v1/poweroff",

                "/api/v1/status"
            ]

            self.sendResponse(data)
        else:
            self.sendResponse('404 Not found', 404)


	#	POST is for submitting data.
    def do_POST(self):
        print("[Http.Post] %s called" % self.path)

        if self.path == '/api/v1/switch':
            data = { 'status': 'False' }
            content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
            post_data = self.rfile.read(content_length) # <--- Gets the data itself
            json_data = json.loads(post_data)
            print("[Http.Post] %s payload (%s)" % (self.path, json_data))
            new_state = json_data.get("active")
            print(new_state)

            console = Xbox.getInstance();
            if console == False:
                # Device is off
                if new_state == True:
                    print("[Http.Post] Turning on Xbox")
                    Xbox.power_on()
                    time.sleep(10) # Sleep 10 seconds to let the xbox turn off so the status is the actual status on next request
                    data = { 'status': True }
                else:
                    data = { 'status': False }
            else:
                # Device is on
                if new_state != True:
                    print("[Http.Post] Turning off Xbox")
                    Xbox.power_off()
                    time.sleep(10) # Sleep 10 seconds to let the xbox turn off so the status is the actual status on next request
                    data = { 'status': False }
                else:
                    data = { 'status': True }

            self.sendResponse(data)
        else:
            self.sendResponse('404 Not found', 404)

    def sendResponse(self, data, status = 200):
        self.send_response(status)
        self.send_header("Content-type", "text/json")
        self.end_headers()

        if status == 404:
            self.wfile.write(bytes("Action not found: %s" % self.path, "utf-8"))
        else:
            self.wfile.write(bytes(json.dumps(data, ensure_ascii=False), "utf-8"))

myServer = HTTPServer((hostName, hostPort), MyServer)
Xbox = Xbox()

print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

try:
	myServer.serve_forever()
except KeyboardInterrupt:
	pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
