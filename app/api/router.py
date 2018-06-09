import json
from gevent.pywsgi import WSGIServer
from console.xbox import Xbox
from api.cache import ApiCache

def HttpRouter(env, start_response):
    apiCache = ApiCache()

    instance = Router(env, start_response, apiCache)
    return instance.handle()

class Router:
    def __init__(self, env, start_response, apiCache):
        self._env = env
        self._start_response = start_response
        self._status = False
        self._cache = apiCache

    def mapRoute(self, path):
        if path == '/':
            return self.action_index()

        if path == '/api/v1/discovery':
            return self.action_discovery()

        if path == '/api/v1/debug':
            return self.action_debug()

        if path == '/api/v1/status':
            return self.action_status()

        if path[:8] == '/api/v1/':
            # Enter device specific api calls
            liveId = path[8:24]
            command = path[24:]

            console = self._cache.findConsoleByLiveId(liveId)
            if (console == False) or (console.state.isConnected() == False):
                if command == '/poweron':
                    return self.action_device_poweron(liveId)
                else:
                    return self.action_index_device(console, liveId)

            else:
                if command == '/':
                    return self.action_index_device(console)

                if command == '/poweroff':
                    return self.action_device_poweroff(console)

                if command[:8] == '/launch/':
                    uri = command[8:]
                    return self.action_device_launch(console, uri)

                if command[:3] == '/ir':
                    param = command[3:]
                    if param == '':
                        return self.action_device_ir(console)
                    else:
                        if param[2] == '/':
                            deviceId = param[1]
                            param = param[3:]
                            return self.action_device_ir(console, param, deviceId)
                        else:
                            return self.action_device_ir(console, param)

                if command == '/poweron':
                    return {
                        'status': 200,
                        'response': 'Xbox is already on'
                    }

                return {
                    'status': 404,
                    'response': 'Not found'
                }


        return False

    def handle(self):
        response = self.mapRoute(self._env['PATH_INFO'])

        if response == False:
            return self.http_response(self._start_response, {
                'status': 404,
                'message': 'Not found'
            }, 404)
        else:
            return self.http_response(self._start_response, response.get('response'), response.get('status'))

    def http_response(self, start_response, data, status=200):
        if status == 404:
            start_response('404 Not Found', [('Content-Type', 'text/json')])
        else:
            start_response('200 OK', [('Content-Type', 'text/json')])

        output_json = bytes(json.dumps(data), "utf-8")
        return [b'%s' % output_json]

    def action_index(self):
        return {
            'status': 200,
            'response': [
                '/api/v1/discovery'
            ]
        }

    def action_discovery(self):
        consoles = Xbox.discover()
        found = []
        for console in consoles:
            found.append(consoles[console].to_json())
            self._cache.foundConsole(console = consoles[console])

        return {
            'status': 200,
            'response': found
        }

    def action_debug(self):
        cache_consoles = self._cache.getConsoles()
        return_consoles = []
        for console in cache_consoles:
            return_consoles.append(cache_consoles[console].to_json())

        return {
            'status': 200,
            'response': {
                'cache': {
                    'consoles': return_consoles
                }
            }
        }

    def action_status(self):
        cache_consoles = self._cache.getConsoles()
        connected_consoles = []
        for console in cache_consoles:
            if cache_consoles[console].state.isConnected() == True:
                connected_consoles.append(cache_consoles[console].to_json())

        return {
            'status': 200,
            'response': {
                'server_status': 'ok',
                'consoles': connected_consoles
            }
        }

    def action_index_device(self, console, liveId = False):
        if console == False:
            return {
                'status': 200,
                'response': [
                    '/api/v1/%s/' % liveId,
                    '/api/v1/%s/poweron' % liveId
                ]
            }
        else:
            return {
                'status': 200,
                'response': [
                    '/api/v1/%s/' % console._console.liveid,
                    '/api/v1/%s/poweron' % console._console.liveid,
                    '/api/v1/%s/poweroff' % console._console.liveid,
                    '/api/v1/%s/status' % console._console.liveid,
                    '/api/v1/%s/launch' % console._console.liveid,
                    '/api/v1/%s/media' % console._console.liveid,
                    '/api/v1/%s/ir' % console._console.liveid,
                ]
            }

    def action_device_poweroff(self, console):
        if console.power_off() == True:
            return {
                'status': 200,
                'response': 'ok'
            }
        else:
            return {
                'status': 500,
                'response': 'Failed to turn off Xbox'
            }



    def action_device_poweron(self, liveId):
        console = Xbox.power_on(liveId)
        if console != False:
            self._cache.foundConsole(console)
            return {
                'status': 200,
                'response': 'Turned on Xbox'
            }
        else:
            return {
                'status': 200,
                'response': 'Failed to turn on Xbox'
            }

    def action_device_launch(self, console, uri):
        if console.launch_uri(uri) == True:
            return {
                'status': 200,
                'response': 'ok'
            }
        else:
            return {
                'status': 200,
                'response': 'failed'
            }

    def action_device_ir(self, console, button = False, deviceId = False):
        if button == False:
            irConfig = console.get_ir_configuration()
            devices = []
            # Get indexdevices = []
            for device_config in irConfig.params:
                buttonLinks = {}
                for button in device_config.buttons:
                    buttonLinks[button] = {
                        'url': '/api/v1/%s/ir/%s/%s' % (console._console.liveid, device_config.device_id, button),
                        'value': device_config.buttons[button]
                    }

                devices.append({
                    'type': device_config.device_type,
                    'brand': device_config.device_brand,
                    'model': device_config.device_model,
                    'id': device_config.device_id,
                    'buttons': buttonLinks
                })
            return {
                'status': 200,
                'response': devices
            }
        else:
            if deviceId != False:
                console._console.send_stump_key(button, deviceId)
            else:
                console._console.send_stump_key(button)
            return {
                'status': 200,
                'response': 'ok'
            }
