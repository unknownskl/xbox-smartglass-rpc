import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

import json
import os

from xbox.sg.console import Console
from xbox.sg.enum import DeviceStatus, ConnectionState, GamePadButton, MediaPlaybackStatus, MediaControlCommand
from xbox.sg.manager import InputManager, TextManager, MediaManager
from xbox.stump.manager import StumpManager

hostName = "0.0.0.0"
hostPort = 8000

class XboxState:
    def __init__(self):
        self.status = False
        self.active_titles = []
        self.mode = 'off'
        self.application = 'none'
        self.build = 0
        self.lastUpdate = 0
        self.lastUpdate_status = 0

    def setStatus(self, status):
        print("[XboxState.setStatus] Set status to %s" % status)
        self.status = status
        self.lastUpdate_status = time.time()
        return True

    def setTitles(self, titles):
        print("[XboxState.setTitles] Updating titles")
        activeTitles = []
        for Title in titles:
            titleStruct = {
                'title_id': Title.title_id,
                'focus': Title.disposition.has_focus,
                'uam_id': Title.aum,
            }

            type = Title.aum.split('!')[1]
            name = Title.aum.split('!')[0]

            if type == 'App':
                if name == '4DF9E0F8.Netflix_mcm4njqhnhss8':
                    self.mode = "video"
                    self.application = "netflix"

                elif name == 'XBMCFoundation.Kodi_4n2hpmxwrvr6p':
                    self.mode = "video"
                    self.application = "kodi"

                elif name == 'SpotifyAB.SpotifyMusic-forXbox_zpdnekdrzrea0':
                    self.mode = "audio"
                    self.application = "spotify"

                else:
                    self.mode = "app"
                    self.application = name+"!App"

            elif type == 'Microsoft.Xbox.LiveTV.Application':
                self.mode = "tv"
                self.application = "livetv"

            elif type == 'Xbox.Dashboard.Application':
                self.mode = "standby"
                self.application = "dashboard"

            elif type == 'Xbox.Settings.Application':
                self.mode = "standby"
                self.application = "settings"

            else:
                self.mode = "game"
                self.application = name+"!"+type

            activeTitles.append(titleStruct)

        self.active_titles = activeTitles
        self.lastUpdate = time.time()
        return self.active_titles

    def setBuild(self, build):
        print("[XboxState.setBuild] Set build to %s" % build)
        self.build = build
        self.lastUpdate = time.time()
        return True

    def getStatus(self):
        return self.status

    def getTitles(self):
        return self.active_titles

    def getMode(self):
        return self.mode

    def getApplication(self):
        return self.application

    def getBuild(self):
        return self.build

    def needsUpdate(self, timeout = 60):
        if self.lastUpdate > (time.time()-timeout):
            print("[XboxState.needsUpdate] Cache expires in %d seconds, return False" % (self.lastUpdate-(time.time()-timeout)))
            return False
        else:
            print("[XboxState.needsUpdate] Needs an update, return True")
            return True

    def statusNeedsUpdate(self, timeout = 30):
        if self.lastUpdate_status > (time.time()-timeout):
            print("[XboxState.statusNeedsUpdate] Cache expires in %d seconds, return False" % (self.lastUpdate_status-(time.time()-timeout)))
            return False
        else:
            print("[XboxState.statusNeedsUpdate] Needs an update, return True")
            return True


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

    # def fetchMediaStatus(self, tries = 1):
    #
    #     print("[Xbox.fetchMediaStatus] called (Try #%d)" % tries)
    #     if tries == 5:
    #         return False
    #
    #     if self.console.title_id == None:
    #         self.console.protocol.serve_forever()
    #         return self.fetchMediaStatus(tries = tries+1)
    #     else:
    #         return self.console.media_state
    #

    def onMediaState(self, state):
        print(state)
        print("[Xbox.onMediaState] called (State: %s)" % state)
        self.console.protocol.shutdown()
        return

    def onTimeout(self):
        self.console.protocol.stop()
        print("[Xbox.onTimeout] Connection timed out")
        self.console = False

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

        if connect == False:
            return self.console
        else:
            print("[Xbox.getInstance] Checking if console data is still up to date")
            console = self.findDevice()
            if console != False:
                print("[Xbox.getInstance] Connecting to Xbox")

                if mode == 'media':
                    print("[Xbox.getInstance] Activated MediaManager (beta)")
                    self.console.add_manager(MediaManager)
                    #self.console.media.on_media_state += self.onMediaState

                if mode == 'stump':
                    print("[Xbox.getInstance] Activated StumpManager (beta)")
                    self.console.add_manager(StumpManager)
                    #self.console.media.on_media_state += self.onMediaState

                state = self.console.connect()

                if state == ConnectionState.Connected:
                    print("[Xbox.getInstance] Xbox Connected")
                    self.console.wait(0.5)
                    connected = True
                else:
                    print("[Xbox.getInstance] [ERROR] Could not connect to Xbox")
                    conected = False
            else:
                print("[Xbox.getInstance] Xbox not found on network")
                connected = False

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
            Console.power_on(os.environ['XBOX_LIVEID'], os.environ['XBOX_IP'], tries=10)
            time.sleep(1)
            Console.power_on(os.environ['XBOX_LIVEID'], os.environ['XBOX_IP'], tries=10)
            time.sleep(1)
            Console.power_on(os.environ['XBOX_LIVEID'], os.environ['XBOX_IP'], tries=10)
            data = True

        else:
            console = self.getInstance(connect = False);
            if console != False:
                print("[Xbox.power_on] Booting xbox from discovery settings(%s, %s)" % (self.console_data.get("address"), self.console.get("liveid")))
                Console.power_on(self.console_data.get("liveid"), self.console.get("address"), tries=10)
                time.sleep(1)
                Console.power_on(self.console_data.get("liveid"), self.console.get("address"), tries=10)
                time.sleep(1)
                Console.power_on(self.console_data.get("liveid"), self.console.get("address"), tries=10)
                data = True
            else:
                data = ['No device found in cache. Turn on your xbox and run /api/v1/discovery']

        return data

    def power_off(self):
        self.console.power_off()
        self.console.wait(1)
        self.console = False
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

            if XboxState.needsUpdate() == True:
                console = Xbox.getInstance();
                print(console)
                if console != False:
                    print("[Http.Get] Returning online console status")
                    status = console.console_status()

                    XboxState.setStatus(True)
                    XboxState.setTitles(status.active_titles)
                    XboxState.setBuild(status.build_number)

                    print("[Http.Get] active_tiles: %s" % XboxState.getTitles() )
                    print("[Http.Get] mode: %s" % XboxState.getMode() )
                    print("[Http.Get] application: %s" % XboxState.getApplication() )
                    print("[Http.Get] build_number: %s" % XboxState.getBuild() )
                    data = {
                        'status': XboxState.getStatus(),
                        'build_number': XboxState.getBuild(),
                        'active': XboxState.getTitles(),
                        'mode': XboxState.getMode(),
                        'application': XboxState.getApplication()
                    }
                    Xbox.close()
                else:
                    print("[Http.Get] Returning offline console status")
                    data = {
                        'status': 'offline',
                        'build_number': XboxState.getBuild(),
                        'active': [],
                        'mode': 'off',
                        'application': 'none'
                    }
            else:
                data = {
                    'status': XboxState.getStatus(),
                    'build_number': XboxState.getBuild(),
                    'active': XboxState.getTitles(),
                    'mode': XboxState.getMode(),
                    'application': XboxState.getApplication()
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

        elif self.path == "/api/v1/ir":
            console = Xbox.getInstance(mode = 'stump');
            tvConfig = console.request_stump_configuration()
            print(tvConfig)

            devices = []
            for device_config in tvConfig.params:
                buttonLinks = {}
                for button in device_config.buttons:
                    buttonLinks[button] = {
                        'url': '/api/v1/ir/%s/%s' % (device_config.device_id, button),
                        'value': device_config.buttons[button]
                    }

                devices.append({
                    'type': device_config.device_type,
                    'brand': device_config.device_brand,
                    'model': device_config.device_model,
                    'id': device_config.device_id,
                    'buttons': buttonLinks
                })


            self.sendResponse(devices)

        elif self.path[:11] == "/api/v1/ir/":
            deviceId = self.path[11];
            if deviceId in '0123':
                button = self.path[13:]
            else:
                button = self.path[11:]
                deviceId = False

            console = Xbox.getInstance(mode = 'stump');
            if deviceId != False:
                command = console.send_stump_key(button, deviceId)
            else:
                command = console.send_stump_key(button)

            self.sendResponse({
                'device_id': deviceId,
                'button': button
            })

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
                'console_data': consoleData,
                #'xbox_state': XboxState
            }
            self.sendResponse(data)

        elif self.path == "/api/v1/switch":
            if XboxState.statusNeedsUpdate() == True:
                console = Xbox.getInstance();
                if console == False:
                    XboxState.setStatus(False)
                    data = { 'status': False }
                else:
                    XboxState.setStatus(True)
                    data = { 'status': True }
                    Xbox.close()
            else:
                data = { 'status': XboxState.getStatus() }

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
            print("[Http.Post] set status to: %s" % new_state)

            if XboxState.statusNeedsUpdate() == True:
                print("[Http.Post] Turning off console")
                console = Xbox.getInstance();
                if console == False:
                    # Device is off
                    if new_state == True:
                        print("[Http.Post] Turning on console")
                        Xbox.power_on()
                        time.sleep(10) # Sleep 10 seconds to let the xbox turn off so the status is the actual status on next request
                        data = { 'status': True }
                    else:
                        data = { 'status': False }
                else:
                    # Device is on
                    if new_state != True:
                        print("[Http.Post] Turning off console")
                        Xbox.power_off()
                        time.sleep(10) # Sleep 10 seconds to let the xbox turn off so the status is the actual status on next request
                        data = { 'status': False }
                    else:
                        data = { 'status': True }
            else:
                if XboxState.getStatus() == True:
                    # Device is on
                    if new_state == False:
                        print("[Http.Post] Turning off console")
                        console = Xbox.getInstance();
                        if console != False:
                            Xbox.power_off()
                            XboxState.setStatus(False)
                            print("[Http.Post] Turned off console")
                        else:
                            print("[Http.Post] Could not turn off console")
                else:
                    # Device is off
                    if new_state == True:
                        print("[Http.Post] Turning on console")
                        Xbox.power_on()
                        console = Xbox.getInstance();
                        if console != False:
                            print("[Http.Post] Turned on console")
                            XboxState.setStatus(True)
                        else:
                            print("[Http.Post] Could not turn on console")
                            XboxState.setStatus(False)

            data = { "status": XboxState.getStatus() }

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
XboxState = XboxState()

print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

try:
	myServer.serve_forever()
except KeyboardInterrupt:
	pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
