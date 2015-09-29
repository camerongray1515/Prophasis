from plugin import PluginInterface, PluginResult

class Plugin(PluginInterface):
    def get_data(self):
        return PluginResult(1, "This is a message")