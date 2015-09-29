import os
import json
from agent_config import get_config

config = get_config()
plugin_repo_dir = os.path.normpath(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), config["plugin_repo"]))

if not os.path.isdir(plugin_repo_dir):
    raise SystemExit("Plugin repository does not exist at path: {0}".format(
        plugin_repo_dir))

def get_manifest_for_plugin(plugin_id):
    for directory in os.listdir(plugin_repo_dir):
        manifest_file = os.path.join(plugin_repo_dir, directory,
            "manifest.json")
        try:
            with open(manifest_file, "r") as f:
                manifest = json.load(f)
        except FileNotFoundError:
            raise SystemExit("Manifest file could not be found for plugin {0}"
                "".format(directory))
        try:
            if manifest["id"] == plugin_id:
                return manifest
        except KeyError:
            raise SystemExit("Manifest file for plugin {0} does not contain an"
                " id attribute".format(directory))

    return None
