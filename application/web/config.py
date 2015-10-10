import json
import os

from binascii import hexlify

config_file_path = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "config.json")

def get_config():
    try:
        with open(config_file_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        raise SystemExit("Config file, config.json not found in web "
            "directory, perhaps you need to run the web setup script?")

    required_fields = ["temp_dir"]
    for field in required_fields:
        if field not in config:
            raise SystemExit("Config file does not contain an entry for {0} "
                "you must rectify this in order to continue".format(field))

    return config

def get_config_value(config, key):
    try:
        return config[key]
    except KeyError:
        raise SystemExit("Key \"{0}\" does not exist in config.json, did you "
            "run setup?".format(key))