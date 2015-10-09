from flask import Blueprint, jsonify, request
from responses import error_response
from models import create_all, session, Host, HostGroup, HostGroupAssignment
from sqlalchemy import or_, and_

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

@api.route("/hosts/edit/", methods=["POST"])
def hosts_edit():
    host_id = request.form.get("host-id")
    name = request.form.get("name")
    host = request.form.get("host")
    description = request.form.get("description")
    auth_key = request.form.get("auth-key")

    if not (name and host and auth_key):
        return error_response("Name, host and auth key are required")

    hosts = Host.query.filter(and_(or_(Host.name == name, Host.host == host),
        Host.id != host_id)).count()
    if hosts:
        return error_response("A host with that name or host already exists")

    h = Host.query.get(host_id)
    if not h:
        return error_response("Host could not be found!")

    h.id = host_id
    h.name = name
    h.host = host
    h.description = description
    h.auth_key = auth_key

    session.commit()

    return jsonify(success=True, message="Host has been saved successfully")

@api.route("/host-groups/add/", methods=["POST"])
def host_groups_add():
    name = request.form.get("name")
    description = request.form.get("description")
    hosts = request.form.getlist("hosts[]")
    host_groups = request.form.getlist("host-groups[]")

    if not name:
        return error_response("You must supply a name for this group")

    groups = HostGroup.query.filter(HostGroup.name == name).count()
    if groups:
        return error_response("A group with that name already exists")

    host_group = HostGroup(name=name, description=description)
    session.add(host_group)
    session.commit()

    for host in hosts:
        a = HostGroupAssignment(host_group_id=host_group.id,
            member_host_id=host)
        session.add(a)

    for group in host_groups:
        a = HostGroupAssignment(host_group_id=host_group.id,
            member_host_group_id=group)
        session.add(a)

    session.commit()

    return jsonify(success=True, message="Host Group added successfully")

@api.route("/host-groups/edit/", methods=["POST"])
def host_groups_edit():
    host_group_id = request.form.get("host-group-id")
    name = request.form.get("name")
    description = request.form.get("description")
    hosts = request.form.getlist("hosts[]")
    host_groups = request.form.getlist("host-groups[]")

    if not name:
        return error_response("You must supply a name for this group")

    groups = HostGroup.query.filter(and_(HostGroup.name == name,
        HostGroup.id != host_group_id)).count()
    if groups:
        return error_response("A group with that name already exists")

    g = HostGroup.query.get(host_group_id)
    if not g:
        return error_response("Host Group could not be found!")

    g.name = name
    g.description = description

    # Remove all current assignments, they will be replaced with the new ones
    HostGroupAssignment.query.filter(
        HostGroupAssignment.host_group_id == host_group_id).delete()

    for host in hosts:
        a = HostGroupAssignment(host_group_id=host_group_id,
            member_host_id=host)
        session.add(a)

    for group in host_groups:
        a = HostGroupAssignment(host_group_id=host_group_id,
            member_host_group_id=group)
        session.add(a)

    session.commit()

    return jsonify(success=True,
        message="Host Group has been saved successfully")