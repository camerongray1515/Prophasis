import uuid
import os
import tarfile
import json
import shutil
from flask import Blueprint, jsonify, request
from responses import error_response
from models import create_all, session, Host, HostGroup, HostGroupAssignment,\
    Plugin, CheckPlugin, CheckAssignment, Check
from sqlalchemy import or_, and_
from config import get_config, get_config_value
api = Blueprint("api", __name__, url_prefix="/api")

config = get_config()

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

@api.route("/host-groups/delete/", methods=["POST"])
def host_groups_delete():
    host_group_id = request.form.get("host-group-id")

    g = HostGroup.query.get(host_group_id)
    if not g:
        return error_response("Host Group could not be found!")

    session.delete(g)
    session.commit()

    return jsonify(success=True,
        message="Host Group has been deleted successfully")

@api.route("/plugins/install/", methods=["POST"])
def plugins_install():
    plugin_file = request.files.get("plugin")
    if not plugin_file:
        return error_response("File not specified")

    allow_overwrite = request.args.get("allow-overwrite")

    temp_dir_path = get_config_value(config, "temp_dir")
    plugin_repo = get_config_value(config, "plugin_repo")
    filename = str(uuid.uuid4())
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

    plugin_temp_path = os.path.join(temp_dir_path, filename)

    try:
        directory = os.listdir(plugin_temp_path)[0]
        with open(os.path.join(plugin_temp_path, directory,
            "manifest.json")) as f:
            manifest = json.load(f)
    except (KeyError, FileNotFoundError):
        return error_response("Manifest could not be found within the "
            "plugin archive")

    try:
        p = Plugin.query.get(manifest["id"])
    except KeyError:
        return error_response("ID could not be found in plugin manifest "
            "file")

    if not allow_overwrite and p:
        return jsonify(success=True, result="plugin_exists")

    oldfile = None
    if p:
        oldfile = p.archive_file
    else:
        p = Plugin()

    try:
        p.id = manifest["id"]
        p.name = manifest["name"]
        p.description = manifest["description"]
        p.version = manifest["version"]
        p.archive_file = filename + ".tar.gz"
    except KeyError:
        return error_response("Manifest file is missing some requied keys")

    if oldfile:
        try:
            os.remove(os.path.join(plugin_repo, oldfile))
        except FileNotFoundError:
            # We don't care if the file doesn't exist as we are deleting it
            pass
    else:
        session.add(p)

    shutil.move(os.path.join(temp_dir_path, p.archive_file),
        plugin_repo)
    session.commit()

    if oldfile:
        return jsonify(success=True, result="plugin_updated")
    else:
        return jsonify(success=True, result="plugin_installed")

@api.route("/plugins/delete/", methods=["POST"])
def plugins_delete():
    plugin_id = request.form.get("plugin-id")
    
    p = Plugin.query.get(plugin_id)
    if not p:
        return error_response("Plugin does not exist")

    plugin_repo = get_config_value(config, "plugin_repo")
    try:
        os.remove(os.path.join(plugin_repo, p.archive_file))
    except FileNotFoundError:
        # We are deleting so we don't care if the file doesn't exist
        pass

    session.delete(p)
    session.commit()

    return jsonify(success=True,
        message="Plugin has been deleted successfully")

@api.route("/scheduling/add/", methods=["POST"])
def scheduling_add():
    name = request.form.get("name")
    interval_starts = request.form.getlist("interval-start[]")
    interval_values = request.form.getlist("interval-value[]")
    interval_units = request.form.getlist("interval-unit[]")
    hosts = request.form.getlist("hosts[]")
    host_groups = request.form.getlist("host-groups[]")

    if not name:
        return error_response("You must supply a name for this schedule")

@api.route("/checks/add/", methods=["POST"])
def checks_add():
    name = request.form.get("name")
    description = request.form.get("description")
    host_groups = request.form.getlist("host-groups[]")
    hosts = request.form.getlist("hosts[]")
    plugins = request.form.getlist("plugins[]")

    if not name:
        return error_response("You must supply a name for this check")

    c = Check(name=name, description=description)
    session.add(c)
    session.commit()

    for host_id in hosts:
        ca = CheckAssignment(host_id=host_id, check_id=c.id)
        session.add(ca)

    for host_group_id in host_groups:
        ca = CheckAssignment(host_group_id=host_group_id, check_id=c.id)
        session.add(ca)

    for plugin_id in plugins:
        cp = CheckPlugin(plugin_id=plugin_id, check_id=c.id)
        session.add(cp)

    session.commit()

    return jsonify(success=True, message="Check has been added successfully!")

@api.route("/checks/delete/", methods=["POST"])
def checks_delete():
    check_id = request.form.get("check-id")
    check = Check.query.get(check_id)

    if not check:
        return error_response("The check you are trying to delete could not "
            "be found")

    session.delete(check)
    session.commit()

    return jsonify(success=True,
        message="Check has been deleted successfully!")

@api.route("/checks/edit/", methods=["POST"])
def checks_edit():
    name = request.form.get("name")
    description = request.form.get("description")
    host_groups = request.form.getlist("host-groups[]")
    hosts = request.form.getlist("hosts[]")
    plugins = request.form.getlist("plugins[]")
    check_id = request.form.get("check-id")

    if not name:
        return error_response("You must supply a name for this check")

    c = Check.query.get(check_id)

    if not c:
        return error_response("Check could not be found!")

    c.name = name
    c.description = description

    session.commit()

    CheckAssignment.query.filter(CheckAssignment.check_id == check_id).delete()
    CheckPlugin.query.filter(CheckPlugin.check_id == check_id).delete()
    for host_id in hosts:
        ca = CheckAssignment(host_id=host_id, check_id=c.id)
        session.add(ca)

    for host_group_id in host_groups:
        ca = CheckAssignment(host_group_id=host_group_id, check_id=c.id)
        session.add(ca)

    for plugin_id in plugins:
        cp = CheckPlugin(plugin_id=plugin_id, check_id=c.id)
        session.add(cp)

    session.commit()

    return jsonify(success=True, message="Check has been saved successfully!")