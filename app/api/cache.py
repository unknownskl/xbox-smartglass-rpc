class ApiCache:
    _consoles = {}
    _activeConnections = {}

    def foundConsole(self, console):
        if console.getName() in ApiCache._consoles:
            print('[ApiCache.foundConsole] Console already in cache, ignoring: %s' % console.to_json())
        else:
            print('[ApiCache.foundConsole] Adding console to cache: %s' % console.to_json())
            console.connect()
            ApiCache._consoles[console.getName()] = console

    def getConsoles(self):
        print('[ApiCache.getConsoles] Getting consoles from cache')
        return ApiCache._consoles
