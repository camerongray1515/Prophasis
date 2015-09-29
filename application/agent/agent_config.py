import json
import os

def get_config():
    config_file_path = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "config.json")

    try:
        with open(config_file_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        raise SystemExit("Config file, config.json not found in agent "
            "directory, perhaps you need to run the agent setup script?")

    required_fields = ["plugin_repo"]
    for field in required_fields:
        if field not in config:
            raise SystemExit("Config file does not contain an entry for {0} "
                "you must rectify this in order to continue".format(field))

    return config