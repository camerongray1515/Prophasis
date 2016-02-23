from .models import Alert, Host, Plugin, Check
from .application_logging import log_message
from importlib.machinery import SourceFileLoader
import os

module_dir = os.path.normpath(os.path.join(os.path.dirname(
    os.path.realpath(__file__)),"alert_modules"))

def process_alerts(host_id, plugin_id, check_id, old_health, new_health):
    host = Host.query.get(host_id)
    valid_alerts = []
    for alert in host.alerts:
        if not alert.restrict_to_entities:
            valid_alerts.append(alert)
        elif plugin_id in alert.entity_plugin_ids:
            valid_alerts.append(alert)
        elif check_id in alert.entity_check_ids:
            valid_alerts.append(alert)

    for alert in valid_alerts:
        if new_health != old_health and \
            old_health in alert.transitions_from_states and \
            new_health in alert.transitions_to_states:
            plugin = Plugin.query.get(plugin_id)
            check = Check.query.get(check_id)

            message = ("The following alert has been triggered:\n"
                "Alert: {}\n"
                "Host: {}\n"
                "Plugin: {}\n"
                "Check: {}\n"
                "Health state changed from {} to {}").format(alert.name,
                    host.name, plugin.name, check.name, old_health,
                    new_health)

            send_alert(alert.id, message)


class AlertExecutionError(Exception):
    pass

def get_alert_modules():
    modules = []
    for filename in os.listdir(module_dir):
        if os.path.isdir(os.path.join(module_dir, filename)):
            continue
        try:
            module_id = filename.replace(".py", "")
            module = SourceFileLoader("module.{}".format(module_id),
                os.path.join(module_dir, filename)).load_module()
            module_data = {
                "name": module.module_name,
                "id": module_id,
                "config": module.config
            }
            modules.append(module_data)
        except Exception as e:
            raise
            log_message("Alerting", "Could not read data from an alert module")

    return modules

def send_alert(alert_id, message, log_errors=True):
    alert = Alert.query.get(alert_id)

    module_config = {}
    for option in alert.module_options:
        module_config[option.key] = option.value

    try:
        module_found = False
        for module in get_alert_modules():
            if module["id"] == alert.module:
                module_found = True

        if not module_found:
            raise AlertExecutionError("Module not found!")

        module = SourceFileLoader("module.{}".format(alert.module),
            os.path.join(module_dir, "{}.py".format(alert.module))).load_module()
        module.config = module_config
        module.handle_alert(message)
    except AlertExecutionError as ex:
        if log_errors:
            log_message("Alerting - {}".format(alert.module), str(ex))
        else:
            raise
    except Exception as ex:
        if log_errors:
            log_message("Alerting - {}".format(alert.module), "Could not read "
                "data from alert module: {}".format(alert.module))
        else:
            raise AlertExecutionError(str(ex))

if __name__ == "__main__":
    print(get_alert_modules())
