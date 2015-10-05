from flask import Blueprint, jsonify, request

api = Blueprint("api", __name__, url_prefix="/api")

@api.route("/hosts/add/", methods=["POST"])
def hosts_add():
    return jsonify(success=True, message="Host added successfully")