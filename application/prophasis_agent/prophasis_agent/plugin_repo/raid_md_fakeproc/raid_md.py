import re
from plugin import PluginInterface, PluginResult

# Value is the number of failed disks across all arrays, message contains a list
# of degraded arrays
class Plugin(PluginInterface):
    def get_data(self):
        degraded_arrays = []
        total_failed = 0
        with open("/tmp/mdstat", "r") as f:
            current_device = None
            for line in f:
                # Does the line contain the name of the device?
                m = re.search("(.*) : .*", line)
                if m:
                    current_device = m.group(1)

                # Does the line contain information about the number of disks
                m = re.search("\[(\d)/(\d)\] \[.*\]", line)
                if m:
                    num_devices = int(m.group(1))
                    working_devices = int(m.group(2))
                    failed_devices = num_devices - working_devices
                    if failed_devices:
                        degraded_arrays.append(current_device)

                    total_failed += failed_devices
        return PluginResult(value=total_failed,
            message=",".join(degraded_arrays))

if __name__ == "__main__":
    p = Plugin()
    print(p.get_data())
