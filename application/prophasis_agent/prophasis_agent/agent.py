import os
import uuid
import tarfile
import json
import hashlib
from flask import Flask, jsonify, request, Response
from .plugin_handling import get_plugin_metadata, get_data_from_plugin
from .exceptions import PluginExecutionError
from .agent_config import get_config, get_config_value
from functools import wraps
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from shutil import rmtree
agent = Flask(__name__)

def error_response(error_message):
    return jsonify({"success": False, "message": error_message})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        salt, correct_hash = get_config_value(config, "auth_key_hash").split(
            "|")
        auth_valid = False

        if auth and correct_hash:
            to_hash = (salt + auth.password).encode("ascii")
            key_correct = hashlib.sha256(to_hash).hexdigest() == correct_hash

            if auth.username == "core" and key_correct:
                auth_valid = True

        if not auth_valid:
            return Response("Auth required", 401,
                {"WWW-Authenticate": "Basic realm=\"Auth Required\""})
        return f(*args, **kwargs)
    return decorated

@agent.route("/check-plugin-version/")
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

@agent.route("/get-plugin-data/")
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

@agent.route("/ping/")
@requires_auth
def ping():
    return jsonify({"success": True, "message": "pong"})

@agent.route("/update-plugin/", methods=["POST"])
@requires_auth
def update_plugin():
    plugin_file = request.files.get("plugin")
    if not plugin_file:
        return error_response("File not specified")

    temp_dir_path = get_config_value(config, "temp_dir")
    plugin_repo = get_config_value(config, "plugin_repo")
    filename = str(uuid.uuid4())
    try:
        try:
            plugin_file.save(os.path.join(temp_dir_path,
                filename + ".tar.gz"))
        except Exception as e:
            return error_response("Failed to create tempoary file: {0}".format(
                str(e)))

        try:
            plugin_archive = tarfile.open(os.path.join(temp_dir_path,
                filename + ".tar.gz"))
            os.mkdir(os.path.join(temp_dir_path, filename))

            plugin_archive.extractall(os.path.join(temp_dir_path, filename))
        except Exception as e:
            return error_response("Failed to extract plugin: {0}".format(
                str(e)))

        # Figure out the name of the directory containing the plugin, if there
        # is more than one file/directory in the temp directory, raise an error
        # as the tar file is most likely not correctly formatted
        files = os.listdir(os.path.join(temp_dir_path, filename))
        if len(files) != 1 or not os.path.isdir(os.path.join(temp_dir_path,
            filename, files[0])):
            return error_response("Plugin archive appears to be malformed")

        try:
            with open(os.path.join(temp_dir_path, filename, files[0],
                "manifest.json"), "r") as f:
                manifest = json.load(f)
                plugin_id = manifest["id"]
        except (FileNotFoundError, KeyError) as e:
            return error_response("Manifest file could not be read: {0}"
                "".format(str(e)))

        # Do the actual installation by deleting any current versions of the
        # plugin and then copying the uploaded version into the repo
        (directory, _) = get_plugin_metadata(plugin_id)
        if directory:
            rmtree(os.path.join(plugin_repo, directory))
        os.rename(os.path.join(temp_dir_path, filename, files[0]),
            os.path.join(plugin_repo, files[0]))

        return jsonify({"success": True})
    finally:
        try:
            os.remove(os.path.join(temp_dir_path, filename + ".tar.gz"))
            rmtree(os.path.join(temp_dir_path, filename))
        except FileNotFoundError:
            pass # We don't care if either file doesn't exist

def main():
    config = get_config()
    print("Agent starting up...")
    # Create directories if they don't exist
    for directory in ["plugin_repo", "temp_dir"]:
        dir_path = get_config_value(config, directory)
        if not os.path.isdir(dir_path):
            print("Creating directory at {0}".format(dir_path))
            os.mkdir(dir_path)

    if get_config_value(config, "use_ssl"):
        http_server = HTTPServer(WSGIContainer(agent),
            ssl_options={
                "certfile": get_config_value(config, "ssl_crt"),
                "keyfile": get_config_value(config, "ssl_key")
            })
    else:
        http_server = HTTPServer(WSGIContainer(agent))

    http_server.listen(get_config_value(config, "port"))
    print("Running!")
    IOLoop.instance().start()

if __name__ == "__main__":
    main()
