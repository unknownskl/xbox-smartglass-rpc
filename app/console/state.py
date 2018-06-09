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
        return self.active_titles
