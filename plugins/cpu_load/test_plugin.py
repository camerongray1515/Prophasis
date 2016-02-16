import os
import multiprocessing
from prophasis_agent.plugin import PluginInterface, PluginResult

class Plugin(PluginInterface):
    def get_data(self):
        # 1 Minute load average adjusted by number of CPUs to give a percentage
        # adjusted by the number of CPUs in the system
        (avg, _, _) = os.getloadavg()
        percentage = (avg / multiprocessing.cpu_count()) * 100
        return PluginResult(percentage)
