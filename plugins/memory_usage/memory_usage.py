import psutil
from prophasis_agent.plugin import PluginInterface, PluginResult

class Plugin(PluginInterface):
    def get_data(self):
        return PluginResult(psutil.virtual_memory().percent)
