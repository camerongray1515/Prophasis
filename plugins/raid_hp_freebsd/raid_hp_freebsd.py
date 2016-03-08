import re
import subprocess
from prophasis_agent.plugin import PluginInterface, PluginResult

# Value is the number of failed disks across all arrays, message contains a list
# of degraded arrays
class Plugin(PluginInterface):
    def get_data(self):
        degraded_arrays = []

        try:
            result = subprocess.check_output("sudo camcontrol devlist",
                shell=True)
        except subprocess.CalledProcessError as ex:
            return PluginResult(message="ERROR: {}".format(ex.output))

        for line in result.split("\n"):
            m = re.search("<.* (.*)>.*\(pass[0-9]+,(da[0-9]+)\)", line)
            if m:
                status = m.group(1)
                device = m.group(2)

                if not status.upper() == "OK":
                    degraded_arrays.append(device)

        return PluginResult(value=len(degraded_arrays),
            message=",".join(degraded_arrays))
