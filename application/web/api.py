from flask import Blueprint, jsonify, request
from responses import error_response
from models import create_all, session, Host

api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/hosts/add/", methods=["POST"])
def hosts_add():
    name = request.form.get("name")
    host = request.form.get("host")
    description = request.form.get("description")
    auth_key = request.form.get("auth-key")

    if not (name and host and auth_key):
        return error_response("Name, host and auth key are required")

    hosts = Host.query.filter(Host.name == name or Host.host == host).count()
    if hosts:
        return error_response("A host with that name or host already exists")

    h = Host(name=name, host=host, description=description,
        auth_key=auth_key)
    session.add(h)
    session.commit()

    return jsonify(success=True, message="Host added successfully")

@api.route("/hosts/delete/", methods=["POST"])
def hosts_delete():
    host_id = request.form.get("host-id")

    h = Host.query.get(host_id)
    if not h:
        return error_response("Host could not be found!")

    session.delete(h)
    session.commit()

    return jsonify(success=True, message="Host has been deleted successfully")