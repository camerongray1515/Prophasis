from syslog import syslog

module_name = "Syslog"

config = {
    "prefix": "Default Prefix"
}

def handle_alert(message):
    syslog("{} - {}".format(config["prefix"], message))
