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
