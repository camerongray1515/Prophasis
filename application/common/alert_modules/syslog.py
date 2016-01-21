from syslog import syslog

config = {
    "prefix": "Default Prefix"
}

def handle_alert(message):
    syslog("{} - {}".format(config["prefix"], message))
