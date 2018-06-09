class XboxState:
    def __init__(self):
        self.connected = False
        self.active_titles = []
        self.mode = False
        self.application = False
        self.build = False

    def to_json(self):
        return {
            'connected': self.connected,
            'mode': self.mode,
            'application': self.application
        }

    def setConnected(self, state):
        self.connected = state

    def isConnected(self):
        return self.connected

    def setMode(self, mode):
        if self.mode != mode:
            print("[XboxState.setMode] Changing mode to: %s" % mode)
            self.mode = mode

    def setApplication(self, application):
        if self.application != application:
            print("[XboxState.setMode] Changing application to: %s" % application)
            self.application = application

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
                    self.setMode("video")
                    self.setApplication("netflix")

                elif name == 'XBMCFoundation.Kodi_4n2hpmxwrvr6p':
                    self.setMode("video")
                    self.setApplication("kodi")

                elif name == 'SpotifyAB.SpotifyMusic-forXbox_zpdnekdrzrea0':
                    self.setMode("audio")
                    self.setApplication("spotify")

                else:
                    self.setMode("app")
                    self.setApplication(name+"!App")

            elif type == 'Microsoft.Xbox.LiveTV.Application':
                self.setMode("tv")
                self.setApplication("livetv")

            elif type == 'Xbox.Dashboard.Application':
                self.setMode("standby")
                self.setApplication("dashboard")

            elif type == 'Xbox.Settings.Application':
                self.setMode("standby")
                self.setApplication("settings")

            else:
                self.setMode("game")
                self.setApplication(name+"!"+type)

            activeTitles.append(titleStruct)

        self.active_titles = activeTitles
        return self.active_titles
