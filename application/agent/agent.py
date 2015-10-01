import argparse
import bcrypt
from flask import Flask, jsonify, request, Response
from plugin_handling import get_plugin_metadata, get_data_from_plugin
from exceptions import PluginExecutionError
from agent_config import get_config, setup_wizard, get_config_value
from functools import wraps
from tornado.wsgi import WSGIContainer
from tornado import httpserver
from tornado.ioloop import IOLoop
agent = Flask(__name__)

parser = argparse.ArgumentParser()
g = parser.add_mutually_exclusive_group(required=True)
g.add_argument("--run-server", action="store_true")
g.add_argument("--setup", action="store_true")
args = parser.parse_args()

def error_response(error_message):
    return jsonify({"success": False, "error": error_message})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        correct_key_hash = get_config_value(config, "auth_key_hash").encode(
            "ascii")

        auth_valid = False

        if auth and correct_key_hash:
            key_correct = bcrypt.hashpw(auth.password.encode("ascii"),
                correct_key_hash) == correct_key_hash

            if auth.username == "core" and key_correct:
                auth_valid = True

        if not auth_valid:
            return Response("Auth required", 401,
                {"WWW-Authenticate": "Basic realm=\"Auth Required\""})
        return f(*args, **kwargs)
    return decorated

@agent.route("/check-plugin-version")
@requires_auth
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
@requires_auth
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
    if args.run_server:
        config = get_config()
        if get_config_value(config, "use_ssl"):
            pass
        else:
            http_server = httpserver.HTTPServer(WSGIContainer(agent))

        http_server.listen(get_config_value(config, "port"))
        IOLoop.instance().start()
    elif args.setup:
        setup_wizard()
