import os
from flask import Flask, render_template, abort
from flask.ext.login import LoginManager, login_required, logout_user
from api import api
from reports import reports
from models import Host, HostGroup, HostGroupAssignment, Plugin, Check,\
    CheckAssignment, CheckPlugin, Schedule, ScheduleCheck, ScheduleInterval,\
    PluginThreshold, User, Service
from datetime import datetime
from jinja2 import Markup

web = Flask(__name__)
web.register_blueprint(api)
web.register_blueprint(reports)
# TODO: Store in config file or something?
web.secret_key = b'\x0bi\xcb\r\x8f\x8f\x06:\x8f\x0b\x0cw\x7f\x8dJ\x0fd\xdbH'\
    b'\x86\x0egNq\xd0n\xa9\xa7\xdd\xb2\xbf\xa9\x13\x1f\xce\x8f\x9a=\xbc.\xcaV'\
    b'\x85zC\xf1\x86Z[e'

# Allows us to include blocks in templates without Jinja parsing them, this is
# useful when we want to pass the template unmodified to the frontend so
# handlebars.js can handle it instead.
web.jinja_env.globals['include_raw'] = lambda f:\
    Markup(web.jinja_loader.get_source(web.jinja_env, f)[0])

login_manager = LoginManager()
login_manager.init_app(web)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@web.route("/login/")
def login():
    return render_template("login.html", nav_section="login", section="Log In",
        title="", not_logged_in=True)

@web.route("/logout/")
@login_required
def logout():
    logout_user()
    return render_template("logout.html", nav_section="logout",
        section="Log Out", title="", not_logged_in=True)

@web.route("/example/")
@login_required
def example():
    return render_template("example.html")

@web.route("/")
@login_required
def home():
    return render_template("home.html", nav_section="home", section="Home")

@web.route("/hosts/")
@login_required
def hosts():
    hosts = Host.query.all()

    return render_template("hosts.html", nav_section="hosts", section="Hosts",
        title="Manage Hosts", hosts=hosts)

@web.route("/hosts/add/")
@login_required
def hosts_add():
    return render_template("host-form.html", nav_section="hosts",
        section="Hosts", title="Add Host", method="add")

@web.route("/hosts/edit/<host_id>/")
@login_required
def hosts_edit(host_id):
    host = Host.query.get(host_id)
    if not host:
        abort(404)

    return render_template("host-form.html", nav_section="hosts",
        section="Hosts", title="Edit Host", method="edit", host=host)

@web.route("/host-groups/")
@login_required
def host_groups():
    host_groups = HostGroup.query.all()

    return render_template("host-groups.html", nav_section="host-groups",
        section="Host Groups", title="Manage Host Groups",
        host_groups=host_groups)

@web.route("/host-groups/add/")
@login_required
def host_groups_add():
    hosts = Host.query.all()
    host_groups = HostGroup.query.all()

    return render_template("host-group-form.html", nav_section="host-groups",
        section="Host Groups", title="Add Host Group", method="add",
        hosts=hosts, host_groups=host_groups)

@web.route("/host-groups/edit/<host_group_id>/")
@login_required
def host_groups_edit(host_group_id):
    host_group = HostGroup.query.get(host_group_id)
    if not host_group:
        abort(404)

    hosts = Host.query.all()
    host_groups = HostGroup.query.all()

    member_host_group_ids = []
    member_host_ids = []
    group_assignments = HostGroupAssignment.query.filter(
        HostGroupAssignment.host_group_id == host_group_id)
    for assignment in group_assignments:
        if assignment.member_host_id:
            member_host_ids.append(assignment.member_host_id)

        if assignment.member_host_group_id:
            member_host_group_ids.append(assignment.member_host_group_id)

    return render_template("host-group-form.html", nav_section="host-groups",
        section="Host Groups", title="Edit Host Group", method="edit",
        host_group=host_group, hosts=hosts, host_groups=host_groups,
        member_host_group_ids=member_host_group_ids,
        member_host_ids=member_host_ids)

@web.route("/plugins/")
@login_required
def plugins():
    plugins = Plugin.query.all()

    return render_template("plugins.html", nav_section="plugins",
        section="Plugins", title="Manage Plugins", plugins=plugins)

@web.route("/plugins/install/")
@login_required
def plugins_install():
    return render_template("plugin-form.html", nav_section="plugins",
        section="Plugins", title="Install Plugin")

@web.route("/plugins/thresholds/<plugin_id>/")
@login_required
def plugins_thresholds(plugin_id):
    p = Plugin.query.get(plugin_id)
    if not p:
        abort(404)

    checks = Check.query.all()
    thresholds = PluginThreshold.query.filter(
        PluginThreshold.plugin_id==plugin_id).order_by(
            PluginThreshold.default.desc()).all()

    # If there is not a default threshold, insert a blank one
    if len(thresholds) == 0 or not thresholds[0].default:
        thresholds.insert(0, PluginThreshold(id=0, default=True,
            classification_code=""))

    max_threshold_id = 0
    for threshold in thresholds:
        if threshold.id > max_threshold_id:
            max_threshold_id = threshold.id

    thresholds.append("template")

    return render_template("plugin-thresholds.html", nav_section="plugins",
        section="Plugins", title="Set Thresholds", plugin=p, checks=checks,
        thresholds=thresholds, max_threshold_id=max_threshold_id)

@web.route("/scheduling/")
@login_required
def scheduling():
    schedules = Schedule.query.all()

    return render_template("scheduling.html", nav_section="scheduling",
        section="Scheduling", title="Manage Schedules", schedules=schedules)

@web.route("/scheduling/add/")
@login_required
def scheduling_add():
    checks = Check.query.all()

    iso_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return render_template("scheduling-form.html", nav_section="scheduling",
        section="Scheduling", title="Add Schedule", method="add",
        checks=checks, iso_datetime=iso_datetime)

@web.route("/scheduling/edit/<schedule_id>/")
@login_required
def scheduling_edit(schedule_id):
    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        abort(404)

    checks = Check.query.all()
    schedule_checks = ScheduleCheck.query.filter(
        ScheduleCheck.schedule_id == schedule_id)
    schedule_intervals = ScheduleInterval.query.filter(
        ScheduleInterval.schedule_id == schedule_id)

    member_check_ids = []
    for check in schedule_checks:
        member_check_ids.append(check.check_id)

    iso_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return render_template("scheduling-form.html", nav_section="scheduling",
        section="Scheduling", title="Edit Schedule", method="edit",
        checks=checks, iso_datetime=iso_datetime, schedule=schedule,
        schedule_intervals=schedule_intervals,
        member_check_ids=member_check_ids)

@web.route("/checks/")
@login_required
def checks():
    checks = Check.query.all()

    return render_template("checks.html", nav_section="checks",
        section="Checks", title="Manage Checks", checks=checks)

@web.route("/checks/add/")
@login_required
def checks_add():
    hosts = Host.query.all()
    host_groups = HostGroup.query.all()
    plugins = Plugin.query.all()

    return render_template("check-form.html", nav_section="checks",
        section="Checks", title="Add Check", hosts=hosts, method="add",
        host_groups=host_groups, plugins=plugins)

@web.route("/checks/edit/<check_id>/")
@login_required
def checks_edit(check_id):
    check = Check.query.get(check_id)
    if not check:
        abort(404)

    assignments = CheckAssignment.query.filter(
        CheckAssignment.check_id == check_id)
    check_plugins = CheckPlugin.query.filter(CheckPlugin.check_id == check_id)

    assigned_host_ids = []
    assigned_host_group_ids = []
    for assignment in assignments:
        if assignment.host_id:
            assigned_host_ids.append(assignment.host_id)
        elif assignment.host_group_id:
            assigned_host_group_ids.append(assignment.host_group_id)

    assigned_plugin_ids = []
    for check_plugin in check_plugins:
        assigned_plugin_ids.append(check_plugin.plugin_id)

    hosts = Host.query.all()
    host_groups = HostGroup.query.all()
    plugins = Plugin.query.all()

    return render_template("check-form.html", nav_section="checks",
        section="Checks", title="Edit Check", hosts=hosts, method="edit",
        host_groups=host_groups, plugins=plugins, check=check,
        assigned_host_ids=assigned_host_ids,
        assigned_host_group_ids=assigned_host_group_ids,
        assigned_plugin_ids=assigned_plugin_ids)

@web.route("/users/")
@login_required
def users():
    users = User.query.all()

    return render_template("users.html", nav_section="users", section="Users",
        title="Manage Users", users=users)

@web.route("/users/add/")
@login_required
def users_add():
    return render_template("user-form.html", nav_section="users",
        section="Users", title="Add User", method="add")

@web.route("/users/edit/<user_id>/")
@login_required
def users_edit(user_id):
    user = User.query.get(user_id)
    if not user:
        abort(404)

    return render_template("user-form.html", nav_section="users",
        section="Users", title="Edit User", method="edit", user=user)

@web.route("/services/")
@login_required
def services():
    services = Service.query.all()

    return render_template("services.html", nav_section="services",
        section="Services", title="Manage Services", services=services)

@web.route("/services/add/")
@login_required
def services_add():
    hosts = Host.query.all()
    host_groups = HostGroup.query.all()

    return render_template("service-form.html", nav_section="services",
        section="Services", title="Add Service", method="add", hosts=hosts,
        host_groups=host_groups)

if __name__ == "__main__":
    web.run(host="0.0.0.0", debug=True)
