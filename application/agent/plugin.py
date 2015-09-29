class PluginInterface:
    def get_data(self):
        raise NotImplementedError

class PluginResult:
    def __init__(self, value, message=""):
        self.value = value
        self.message = message

    def __repr__(self):
        return "<PluginResult value: \"{0}\", message: \"{1}\">".format(self.value,
            self.message)