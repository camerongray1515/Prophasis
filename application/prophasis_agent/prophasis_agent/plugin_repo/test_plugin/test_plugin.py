from plugin import PluginInterface, PluginResult
import os

class Plugin(PluginInterface):
    def get_data(self):
        (avg, _, _) = os.getloadavg()
        return PluginResult(avg)