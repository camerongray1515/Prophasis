import os
import json
import importlib
from .agent_config import get_config, get_config_value
from .exceptions import PluginExecutionError

def get_plugin_repo_dir():
    config = get_config()
    plugin_repo_dir = os.path.normpath(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), get_config_value(config, "plugin_repo")))

    if not os.path.isdir(plugin_repo_dir):
        raise SystemExit("Plugin repository does not exist at path: {0}".format(
            plugin_repo_dir))

    return plugin_repo_dir

def get_plugin_metadata(plugin_id):
    """
        Returns a tuple containing the plugin's directory and its
        manifest or (None, None) if the plugin cannot be found.
    """
    config = get_config()
    plugin_repo_dir = get_plugin_repo_dir()
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
                return (directory, manifest)
        except KeyError:
            raise SystemExit("Manifest file for plugin {0} does not contain an"
                " id attribute".format(directory))

    return (None, None)

def get_data_from_plugin(plugin_id):
    """
        Returns a tuple of (value, message) from the plugin.
        Raises PluginExecutionError
    """
    config = get_config()
    (directory, _) = get_plugin_metadata(plugin_id)

    if not directory:
        raise PluginExecutionError("Plugin could not be found")

    module = importlib.import_module("plugin_repo.{0}".format(directory))
    try:
        plugin = module.Plugin()
    except AttributeError:
        raise PluginExecutionError("Package does not contain \"Plugin\" class")

    try:
        data = plugin.get_data()
    except AttributeError:
        raise PluginExecutionError("Plugin class does not contain get_data() "
            "method")
    except Exception as e:
        raise PluginExecutionError("The following error occured when executing"
            " the plugin: ({0}) {1}".format(type(e).__name__, str(e)))

    return (data.value, data.message)
