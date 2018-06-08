class XboxState:
    def __init__(self):
        self.connected = False

    def to_json(self):
        return {
            'connected': self.connected
        }

    def is_connected(self):
        return self.connected
