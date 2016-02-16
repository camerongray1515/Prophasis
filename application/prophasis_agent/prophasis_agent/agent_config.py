import json
import os
import random
import string
import hashlib
from appdirs import site_config_dir
from binascii import hexlify

config_file_dir = site_config_dir("Prophasis", "Prophasis")
config_file_path = os.path.join(config_file_dir, "agent.conf.json")

def get_config():
    try:
        with open(config_file_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        raise SystemExit("Config file not found, perhaps you need to run the "
            "agent setup script?")

    required_fields = ["plugin_repo"]
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

def generate_authentication_key(n_bits=256):
    if n_bits % 8 != 0:
        raise ValueError("Number of bits must be divisible by 8")
    random_bytes = os.urandom(int(n_bits / 8))
    authentication_key = hexlify(random_bytes).decode("ascii")

    return authentication_key
