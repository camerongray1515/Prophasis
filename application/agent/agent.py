from flask import Flask, jsonify, request
from plugin_handling import get_plugin_metadata, get_data_from_plugin
from exceptions import PluginExecutionError
agent = Flask(__name__)

def error_response(error_message):
    return jsonify({"success": False, "error": error_message})

@agent.route("/check-plugin-version")
def check_plugin_verison():
    plugin_id = request.args.get("plugin-id")
    plugin_version = request.args.get("plugin-version")

    if not (plugin_id and plugin_version):
        return error_response("Plugin ID and version are required")

    (_, manifest) = get_plugin_metadata(plugin_id)
    try:
        if not manifest or manifest["version"] < float(plugin_version):
            # Plugin doesn't exist, therefore we want an update
            return jsonify({"success": True, "update-required": True})
    except ValueError:
        return error_response("Plugin version must be a number")

    return jsonify({"success": True, "update-required": False})

@agent.route("/get-plugin-data")
def get_plugin_data():
    plugin_id = request.args.get("plugin-id")
    if not plugin_id:
        return error_response("Plugin ID is required")

    try:
        (value, message) = get_data_from_plugin(plugin_id)
    except PluginExecutionError as e:
        return error_response(str(e))

    return jsonify({"success": True, "value": value, "message": message})

if __name__ == "__main__":
    agent.run(debug=True)