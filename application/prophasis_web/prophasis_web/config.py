import json
import os
import sys

from binascii import hexlify
from appdirs import site_config_dir

config_file_dir = site_config_dir("Prophasis", "Prophasis")
config_file_path = os.path.join(config_file_dir, "web.conf.json")

def get_config():
    try:
        with open(config_file_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        raise SystemExit("Config file, config.json not found at {0}, perhaps "
            "you need to run the setup script?".format(config_file_path))

    return config

def get_config_value(config, key):
    try:
        return config[key]
    except KeyError:
        raise SystemExit("Key \"{0}\" does not exist in config.json, did you "
            "run setup?".format(key))
