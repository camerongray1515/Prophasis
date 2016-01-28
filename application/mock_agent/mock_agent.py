import json
from flask import Flask, jsonify, request
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

mock_agent = Flask(__name__)

# Since there are no real plugins, do not request updates
@mock_agent.route("/check-plugin-version/")
def check_plugin_verison():
    return jsonify({"success": True, "update-required": False})

@mock_agent.route("/ping/")
def ping():
    print("Received ping for {}".format(request.headers["host"]))
    return jsonify({"success": True, "message": "pong"})

@mock_agent.route("/get-plugin-data/")
def get_plugin_data():
    plugin_id = request.args.get("plugin-id")
    host = request.headers["host"]

    print("Received request for {} on {}".format(plugin_id, host), end="")

    with open("data.json", "r") as data_file:
        data = json.load(data_file)

    if host in data and plugin_id in data[host]:
        print(" Responded!")
        return jsonify({"success": True,
            "value": data[host][plugin_id]["value"],
            "message": data[host][plugin_id]["message"]})

    print(" No Data!")
    return jsonify({"success": False,
        "message": "No data for this host/plugin combination"})

if __name__ == "__main__":
    http_server = HTTPServer(WSGIContainer(mock_agent),
        ssl_options={
            "certfile": "keys/server.crt",
            "keyfile": "keys/server.key"
        })
    http_server.listen(4048)
    print("Running...")
    IOLoop.instance().start()
