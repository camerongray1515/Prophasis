from plugin import PluginInterface, PluginResult

class Plugin(PluginInterface):
    def get_data(self):
        return PluginResult(value=None, message="ok")
