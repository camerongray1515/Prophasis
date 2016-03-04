import uuid
import os
import tarfile
import json
import shutil
import requests
import bcrypt
from requests.exceptions import Timeout, ConnectionError
from flask import Blueprint, jsonify, request
from flask.ext.login import login_required, login_user
from .responses import error_response
from prophasis_common.models import create_all, session, Host, HostGroup,\
    Plugin, CheckPlugin, CheckAssignment, Check, Schedule, ScheduleInterval,\
    ScheduleCheck, PluginThreshold, User, ServiceDependency, Service,\
    RedundancyGroup, RedundancyGroupComponent, Alert, AlertCheckEntity,\
    AlertTransitionTo, AlertTransitionFrom, AlertRestrictToEntity,\
    AlertModuleOption, HostGroupAssignment
from sqlalchemy import or_, and_
from sqlalchemy.exc import SQLAlchemyError
from .config import get_config, get_config_value
from datetime import datetime
from prophasis_common.alerting import send_alert, AlertExecutionError
api = Blueprint("api", __name__, url_prefix="/api")

config = get_config()

@api.route("/login/", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    error_message = "Username or password incorrect"

    users = User.query.filter(User.username == username).all()
    if not users:
        return error_response(error_message)

    password_hash = users[0].password_hash.encode("utf-8")
    if bcrypt.hashpw(password.encode("utf-8"), password_hash) == password_hash:
        login_user(users[0])
        return jsonify(success=True, message="Login Successful!")
    else:
        return error_response(error_message)

@api.route("/hosts/add/", methods=["POST"])
@login_required
def hosts_add():
    name = request.form.get("name")
    host = request.form.get("host")
    description = request.form.get("description")
    auth_key = request.form.get("auth-key")
    check_certificate = bool(request.form.get("check-certificate"))

    if not (name and host and auth_key):
        return error_response("Name, host and auth key are required")

    hosts = Host.query.filter(Host.name == name or Host.host == host).count()
    if hosts:
        return error_response("A host with that name or host already exists")

    success, message  = test_agent_connection(host, auth_key, check_certificate)
    if not success:
        return error_response(message)

    h = Host(name=name, host=host, description=description,
        auth_key=auth_key, check_certificate=check_certificate)
    session.add(h)
    session.commit()

    return jsonify(success=True, message="Host added successfully")

@api.route("/hosts/delete/", methods=["POST"])
@login_required
def hosts_delete():
    host_id = request.form.get("host-id")

    h = Host.query.get(host_id)
    if not h:
        return error_response("Host could not be found!")

    session.delete(h)
    session.commit()

    return jsonify(success=True, message="Host has been deleted successfully")

@api.route("/hosts/edit/", methods=["POST"])
@login_required
def hosts_edit():
    host_id = request.form.get("host-id")
    name = request.form.get("name")
    host = request.form.get("host")
    description = request.form.get("description")
    auth_key = request.form.get("auth-key")
    check_certificate = bool(request.form.get("check-certificate"))

    if not (name and host and auth_key):
        return error_response("Name, host and auth key are required")

    hosts = Host.query.filter(and_(or_(Host.name == name, Host.host == host),
        Host.id != host_id)).count()
    if hosts:
        return error_response("A host with that name or host already exists")

    h = Host.query.get(host_id)
    if not h:
        return error_response("Host could not be found!")

    success, message  = test_agent_connection(host, auth_key, check_certificate)
    if not success:
        return error_response(message)

    h.id = host_id
    h.name = name
    h.host = host
    h.description = description
    h.auth_key = auth_key
    h.check_certificate = check_certificate

    session.commit()

    return jsonify(success=True, message="Host has been saved successfully")

def test_agent_connection(host, auth_key, check_certificate):
    request_url = "https://core:{0}@{1}:4048/ping/".format(auth_key, host)
    try:
        r = requests.get(request_url, verify=check_certificate)
    except (ConnectionError, Timeout) as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            return (False, "Cerfiticate verification failed")
        else:
            return (False, "Could not establish connection with agent")

    if r.status_code == 200:
        return (True, "Connection Successful")
    elif r.status_code == 401:
        return (False, "Authentication key incorrect")
    else:
        return (False, "Connection failed due to unknown error")

@api.route("/host-groups/add/", methods=["POST"])
@login_required
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
    session.flush()

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
@login_required
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
@login_required
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
@login_required
def plugins_install():
    plugin_file = request.files.get("plugin")
    if not plugin_file:
        return error_response("File not specified")
    signature_file = request.files.get("signature")

    allow_overwrite = request.args.get("allow-overwrite")

    temp_dir_path = get_config_value(config, "temp_dir")
    plugin_repo = get_config_value(config, "plugin_repo")
    filename = str(uuid.uuid4())
    try:
        plugin_file.save(os.path.join(temp_dir_path,
            filename + ".tar.gz"))
    except Exception as e:
        return error_response("Failed to create temporary file: {0}".format(
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

    if signature_file:
        try:
            signature_file.save(os.path.join(plugin_repo,
                filename + ".tar.gz.sig"))
        except Exception as e:
            return error_response("Failed to save signature file: {}".format(
                str(e)))

    oldfile = None
    if p:
        oldfile = p.archive_file
        oldsig = p.signature_file
    else:
        p = Plugin()

    try:
        p.id = manifest["id"]
        p.name = manifest["name"]
        p.description = manifest["description"]
        p.version = manifest["version"]
        p.view = manifest["view"]
        if (p.view == "custom"):
            try:
                with open(os.path.join(plugin_temp_path, directory,
                    manifest["view_source"])) as f:
                    p.view_source = f.read()
            except FileNotFoundError:
                return error_response("View source file could not be found")
        p.archive_file = filename + ".tar.gz"
        if signature_file:
            p.signature_file = filename + ".tar.gz.sig"
        else:
            p.signature_file = None
    except KeyError:
        return error_response("Manifest file is missing some requied keys")

    if oldfile:
        try:
            os.remove(os.path.join(plugin_repo, oldfile))
            if oldsig:
                os.remove(os.path.join(plugin_repo, oldsig))
        except FileNotFoundError:
            # We don't care if the file doesn't exist as we are deleting it
            pass
    else:
        session.add(p)
        session.flush()

    # If there is a default classifier in the manifest file, add it
    # Only do this if this is a new installation, i.e. don't overwrite existing
    # classifiers
    if not oldfile and "default_classifier" in manifest \
        and "default_n_historical" in manifest:
        try:
            default_n_historical = int(manifest["default_n_historical"])
        except ValueError:
            return error_response("Value for default_n_historical in manifest "
                "must be an integer")

        try:
            with open(os.path.join(plugin_temp_path, directory,
                manifest["default_classifier"]), "r") as f:
                classification_code = f.read()
        except FileNotFoundError:
            return error_response("Default classifier file could not be found")

        pt = PluginThreshold(plugin_id=p.id, default=True,
            n_historical=manifest["default_n_historical"],
            classification_code=classification_code)
        session.add(pt)

    shutil.move(os.path.join(temp_dir_path, p.archive_file),
        plugin_repo)
    session.commit()

    if oldfile:
        return jsonify(success=True, result="plugin_updated")
    else:
        return jsonify(success=True, result="plugin_installed")

@api.route("/plugins/delete/", methods=["POST"])
@login_required
def plugins_delete():
    plugin_id = request.form.get("plugin-id")

    p = Plugin.query.get(plugin_id)
    if not p:
        return error_response("Plugin does not exist")

    plugin_repo = get_config_value(config, "plugin_repo")
    try:
        os.remove(os.path.join(plugin_repo, p.archive_file))
        if p.signature_file:
            os.remove(os.path.join(plugin_repo, p.signature_file))
    except FileNotFoundError:
        # We are deleting so we don't care if the file doesn't exist
        pass

    session.delete(p)
    session.commit()

    return jsonify(success=True,
        message="Plugin has been deleted successfully")

@api.route("/scheduling/add/", methods=["POST"])
@login_required
def scheduling_add():
    name = request.form.get("name")
    description = request.form.get("description")
    interval_starts = request.form.getlist("interval-start[]")
    interval_values = request.form.getlist("interval-value[]")
    interval_units = request.form.getlist("interval-unit[]")
    checks = request.form.getlist("checks[]")

    if not name:
        return error_response("You must supply a name for this schedule")

    s = Schedule(name=name, description=description)
    session.add(s)
    session.flush()

    for check_id in checks:
        sc = ScheduleCheck(check_id=check_id, schedule_id=s.id)
        session.add(sc)

    for interval in zip(interval_starts, interval_values, interval_units):
        try:
            start_timestamp = datetime.strptime(interval[0], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return error_response("Start timestamp for interval was not "
                "understood")
        si = ScheduleInterval(schedule_id=s.id,
            start_timestamp=start_timestamp)
        try:
            si.set_interval(int(interval[1]), interval[2])
        except ValueError:
            return error_response("Interval must be an integer")
        session.add(si)

    session.commit()

    return jsonify(success=True,
        message="Schedule has been added successfully")

@api.route("/scheduling/edit/", methods=["POST"])
@login_required
def scheduling_edit():
    schedule_id = request.form.get("schedule-id")
    name = request.form.get("name")
    description = request.form.get("description")
    interval_starts = request.form.getlist("interval-start[]")
    interval_values = request.form.getlist("interval-value[]")
    interval_units = request.form.getlist("interval-unit[]")
    checks = request.form.getlist("checks[]")

    if not name:
        return error_response("You must supply a name for this schedule")

    s = Schedule.query.get(schedule_id)
    if not s:
        abort(404)

    s.name = name
    s.description = description

    ScheduleCheck.query.filter(ScheduleCheck.schedule_id == s.id).delete()
    for check_id in checks:
        sc = ScheduleCheck(check_id=check_id, schedule_id=s.id)
        session.add(sc)

    ScheduleInterval.query.filter(
        ScheduleInterval.schedule_id == s.id).delete()
    for interval in zip(interval_starts, interval_values, interval_units):
        try:
            start_timestamp = datetime.strptime(interval[0], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return error_response("Start timestamp for interval was not "
                "understood")
        si = ScheduleInterval(schedule_id=s.id,
            start_timestamp=start_timestamp)
        try:
            si.set_interval(int(interval[1]), interval[2])
        except ValueError:
            return error_response("Interval must be an integer")
        session.add(si)

    session.commit()

    return jsonify(success=True,
        message="Schedule has been saved successfully")

@api.route("/scheduling/delete/", methods=["POST"])
@login_required
def scheduling_delete():
    schedule_id = request.form.get("schedule-id")

    s = Schedule.query.get(schedule_id)
    if not s:
        return error_response("The schedule you are trying to delete does "
            "not exist")

    session.delete(s)
    session.commit()

    return jsonify(success=True, message="Schedule has been deleted "
        "successfully!")

@api.route("/checks/add/", methods=["POST"])
@login_required
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
    session.flush()

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
@login_required
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
@login_required
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

    session.flush()

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

@api.route("/plugins/thresholds/save/", methods=["POST"])
@login_required
def plugins_thresholds_save():
    plugin_id = request.form.get("plugin-id")
    thresholds = list(zip(
        request.form.getlist("check[]"),
        request.form.getlist("n-historical[]"),
        request.form.getlist("classification-code[]")
    ))

    used_check_ids = []
    for threshold in thresholds:
        check_id, n_historical, classification_code = threshold
        if check_id == "-1":
            return error_response("You must specify a check for all thresholds")
        if not n_historical or int(n_historical) < 1:
            return error_response("Number of historical values must be greater "
                "than 0 and must be specified")
        if not classification_code.strip():
            return error_response("You must supply classification code")
        if check_id in used_check_ids:
            return error_response("You cannot have multiple thresholds related "
                "to the same check")
        used_check_ids.append(check_id)

    PluginThreshold.query.filter(PluginThreshold.plugin_id==plugin_id).delete()

    for threshold in thresholds:
        check_id, n_historical, classification_code = threshold
        pt = PluginThreshold(
            plugin_id=plugin_id,
            n_historical=n_historical,
            classification_code=classification_code
        )
        if check_id != "default":
            pt.check_id = check_id
            pt.default = False
        else:
            pt.default = True
        session.add(pt)

    session.commit()

    return jsonify(success=True, message="Thresholds have been saved "
        "successfully!")

@api.route("/users/add/", methods=["POST"])
@login_required
def users_add():
    username = request.form.get("username")
    email = request.form.get("email")
    first_name = request.form.get("first-name")
    last_name = request.form.get("last-name")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm-password")

    if not (username.strip() and email.strip() and first_name.strip() and \
        last_name.strip() and password.strip() and confirm_password.strip()):
        return error_response("All fields are required")

    if password != confirm_password:
        return error_response("Passwords do not match")

    if User.query.filter(User.username==username).count():
        return error_response("A user with that username already exists")

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    u = User(username=username, first_name=first_name, last_name=last_name,
        password_hash=password_hash.decode("utf-8"), email=email)
    session.add(u)
    session.commit()

    return jsonify(success=True, message="User has been added successfully!")

@api.route("/users/delete/", methods=["POST"])
@login_required
def users_delete():
    user_id = request.form.get("user-id")

    u = User.query.get(user_id)
    if not u:
        return error_response(
            "The user you are trying to delete does not exist")

    session.delete(u)
    session.commit()

    return jsonify(success=True, message="User has been deleted successfully!")

@api.route("/users/edit/", methods=["POST"])
@login_required
def users_edit():
    username = request.form.get("username")
    email = request.form.get("email")
    first_name = request.form.get("first-name")
    last_name = request.form.get("last-name")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm-password")
    user_id = request.form.get("user-id")

    if not (username.strip() and email.strip() and first_name.strip() and \
        last_name.strip()):
        return error_response("Username, email, first name and last name "
            "are required")

    if password != confirm_password:
        return error_response("Passwords do not match")

    if User.query.filter(User.username==username).filter(
        User.id != user_id).count():
        return error_response("A user with that username already exists")

    u = User.query.get(user_id)
    if not u:
        return error_response("User could not be found!")

    u.username = username
    u.email = email
    u.first_name = first_name
    u.last_name = last_name

    if password:
        u.password_hash = bcrypt.hashpw(password.encode("utf-8"),
            bcrypt.gensalt()).decode("utf-8")

    session.commit()

    return jsonify(success=True, message="User has been saved successfully!")

@api.route("/services/add/", methods=["POST"])
@login_required
def services_add():
    name = request.form.get("name")
    description = request.form.get("description")
    try:
        dependencies = json.loads(request.form.get("dependencies"))
    except ValueError:
        return error_response("Could not understand format of request sent")

    if not name.strip():
        return error_response("You must specify a name")

    try:
        service = Service(name=name, description=description)
        session.add(service)
        session.flush()

        for dependency in dependencies["dependencies"]:
            if dependency["type"] == "host":
                sd = ServiceDependency(service_id=service.id,
                    host_id=dependency["id"])
            else:
                sd = ServiceDependency(service_id=service.id,
                    host_group_id=dependency["id"])
            session.add(sd)

        for redundancy_group in dependencies["redundancyGroups"]:
            rg = RedundancyGroup(service_id=service.id)
            session.add(rg)
            session.flush()
            sd = ServiceDependency(service_id=service.id,
                redundancy_group_id=rg.id)
            session.add(sd)
            for item in redundancy_group["items"]:
                if item["type"] == "host":
                    rgc = RedundancyGroupComponent(redundancy_group_id=rg.id,
                        host_id=item["id"])
                else:
                    rgc = RedundancyGroupComponent(redundancy_group_id=rg.id,
                        host_group_id=item["id"])
                session.add(rgc)

        session.commit()
    except ValueError:
        session.rollback()
        return error_response("The data sent to the server could not be "
            "understood.  Please refresh the page and try again.")

    return jsonify(success=True, message="Service has been added successfully")

@api.route("/services/delete/", methods=["POST"])
@login_required
def services_delete():
    service_id = request.form.get("service-id")
    s = Service.query.get(service_id)

    if not s:
        return error_response("The service you are trying to delete could not "
            "be found")

    session.delete(s)
    session.commit()

    return jsonify(success=True,
        message="Service has been deleted successfully")

@api.route("/services/edit/", methods=["POST"])
@login_required
def services_edit():
    name = request.form.get("name")
    description = request.form.get("description")
    service_id = request.form.get("service-id")
    try:
        dependencies = json.loads(request.form.get("dependencies"))
    except ValueError:
        return error_response("Could not understand format of request sent")

    if not name.strip():
        return error_response("You must specify a name")

    try:
        service = Service.query.get(service_id)
        if not service:
            return error_response("Service could not be found")
        service.name = name
        service.description = description

        gs = RedundancyGroup.query.filter(
            RedundancyGroup.service_id==service.id)
        for g in gs:
            session.delete(g)

        ds = ServiceDependency.query.filter(
            ServiceDependency.service_id==service.id)
        for d in ds:
            session.delete(d)

        for dependency in dependencies["dependencies"]:
            if dependency["type"] == "host":
                sd = ServiceDependency(service_id=service.id,
                    host_id=dependency["id"])
            else:
                sd = ServiceDependency(service_id=service.id,
                    host_group_id=dependency["id"])
            session.add(sd)

        for redundancy_group in dependencies["redundancyGroups"]:
            rg = RedundancyGroup(service_id=service.id)
            session.add(rg)
            session.flush()
            sd = ServiceDependency(service_id=service.id,
                redundancy_group_id=rg.id)
            session.add(sd)
            for item in redundancy_group["items"]:
                if item["type"] == "host":
                    rgc = RedundancyGroupComponent(redundancy_group_id=rg.id,
                        host_id=item["id"])
                else:
                    rgc = RedundancyGroupComponent(redundancy_group_id=rg.id,
                        host_group_id=item["id"])
                session.add(rgc)

        session.commit()
    except ValueError:
        session.rollback()
        return error_response("The data sent to the server could not be "
            "understood.  Please refresh the page and try again.")

    return jsonify(success=True, message="Service has been saved successfully")

@api.route("/alerts/add/", methods=["POST"])
@login_required
def alerts_add():
    name = request.form.get("name")
    entity_selection = request.form.get("entity-selection")
    host_groups = request.form.getlist("host-groups[]")
    hosts = request.form.getlist("hosts[]")
    checks = request.form.getlist("checks[]")
    services = request.form.getlist("services[]")
    plugins = request.form.getlist("plugins[]")
    from_states = request.form.getlist("from-states[]")
    to_states = request.form.getlist("to-states[]")
    module_selection = request.form.get("module-selection")

    if not name:
        return error_response("You must specify a name for this alert")

    if not from_states or not to_states:
        return error_response("You must specify at least one from state and at "
            "least one to state")

    if not module_selection:
        return error_response("You must select a module to use for this alert")

    alert = Alert(name=name, entity_selection_type=entity_selection,
        module=module_selection)
    session.add(alert)
    session.flush()
    for state in to_states:
        session.add(AlertTransitionTo(alert_id=alert.id, state=state))

    for state in from_states:
        session.add(AlertTransitionFrom(alert_id=alert.id, state=state))

    if entity_selection == "custom":
        added_entity = False
        for host_id in hosts:
            session.add(AlertCheckEntity(alert_id=alert.id, host_id=host_id))
            added_entity = True
        for host_group_id in host_groups:
            session.add(AlertCheckEntity(alert_id=alert.id,
                host_group_id=host_group_id))
            added_entity = True
        for service_id in services:
            session.add(AlertCheckEntity(alert_id=alert.id,
                service_id=service_id))
            added_entity = True

        if not added_entity:
            session.rollback()
            return error_response("You must select at least one entity to alert"
                " for state changes in")

    for check_id in checks:
        session.add(AlertRestrictToEntity(alert_id=alert.id, check_id=check_id))
    for plugin_id in plugins:
        session.add(AlertRestrictToEntity(alert_id=alert.id,
            plugin_id=plugin_id))

    for key in request.form.keys():
        if key.startswith("module-option-"):
            option_key = key.replace("module-option-", "", 1)
            option_value = request.form.get(key)
            session.add(AlertModuleOption(alert_id=alert.id, key=option_key,
                value=option_value))

    session.commit()
    return jsonify(success=True, message="Alert has been added successfully")

@api.route("/alerts/delete/", methods=["POST"])
@login_required
def alerts_delete():
    alert_id = request.form.get("alert-id")
    alert = Alert.query.get(alert_id)
    if not alert:
        return error_response("Alert could not be found!")
    session.delete(alert)
    session.commit()

    return jsonify(success=True, message="Alert has been deleted successfully")

@api.route("/alerts/edit/", methods=["POST"])
@login_required
def alerts_edit():
    name = request.form.get("name")
    alert_id = request.form.get("alert-id")
    entity_selection = request.form.get("entity-selection")
    host_groups = request.form.getlist("host-groups[]")
    hosts = request.form.getlist("hosts[]")
    checks = request.form.getlist("checks[]")
    services = request.form.getlist("services[]")
    plugins = request.form.getlist("plugins[]")
    from_states = request.form.getlist("from-states[]")
    to_states = request.form.getlist("to-states[]")
    module_selection = request.form.get("module-selection")

    if not name:
        return error_response("You must specify a name for this alert")

    alert = Alert.query.get(alert_id)
    if not alert:
        abort(404)

    if not from_states or not to_states:
        return error_response("You must specify at least one from state and at "
            "least one to state")

    alert.name = name
    alert.entity_selection_type = entity_selection
    alert.module = module_selection

    AlertTransitionTo.query.filter(
        AlertTransitionTo.alert_id==alert_id).delete()
    AlertTransitionFrom.query.filter(
        AlertTransitionFrom.alert_id==alert_id).delete()
    AlertCheckEntity.query.filter(AlertCheckEntity.alert_id==alert_id).delete()
    AlertRestrictToEntity.query.filter(
        AlertRestrictToEntity.alert_id==alert_id).delete()

    for state in to_states:
        if state in from_states:
            session.rollback()
            return error_response("You cannot have the same state as both a "
                "\"to\" state and a \"from\" state")
        session.add(AlertTransitionTo(alert_id=alert.id, state=state))

    for state in from_states:
        session.add(AlertTransitionFrom(alert_id=alert.id, state=state))

    if entity_selection == "custom":
        added_entity = False
        for host_id in hosts:
            session.add(AlertCheckEntity(alert_id=alert.id, host_id=host_id))
            added_entity = True
        for host_group_id in host_groups:
            session.add(AlertCheckEntity(alert_id=alert.id,
                host_group_id=host_group_id))
            added_entity = True
        for service_id in services:
            session.add(AlertCheckEntity(alert_id=alert.id,
                service_id=service_id))
            added_entity = True

        if not added_entity:
            session.rollback()
            return error_response("You must select at least one entity to alert"
                " for state changes in")

    for check_id in checks:
        session.add(AlertRestrictToEntity(alert_id=alert.id, check_id=check_id))
    for plugin_id in plugins:
        session.add(AlertRestrictToEntity(alert_id=alert.id,
            plugin_id=plugin_id))

    AlertModuleOption.query.filter(
        AlertModuleOption.alert_id==alert.id).delete()
    for key in request.form.keys():
        if key.startswith("module-option-"):
            option_key = key.replace("module-option-", "", 1)
            option_value = request.form.get(key)
            session.add(AlertModuleOption(alert_id=alert.id, key=option_key,
                value=option_value))

    session.commit()
    return jsonify(success=True, message="Alert has been saved successfully")

@api.route("/alerts/test/", methods=["POST"])
@login_required
def alerts_test():
    # TODO: Move most of this logic into alerting
    alert_id = request.form.get("alert-id")
    alert = Alert.query.get(alert_id)
    if not alert:
        return error_response("Alert could not be found!")

    try:
        send_alert(alert.id,
            "This is a test message from the alert \"{}\"".format(alert.name),
            log_errors=False)
    except AlertExecutionError as ex:
        return jsonify(success=False, message=str(ex))

    return jsonify(success=True, message="A test message has been sent using "
        "this alert")
