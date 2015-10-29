from flask import Flask, render_template, abort
from api import api
from models import Host, HostGroup, HostGroupAssignment, Plugin, Check,\
    CheckAssignment, CheckPlugin, Schedule, ScheduleCheck, ScheduleInterval,\
    PluginThreshold, User
from datetime import datetime

web = Flask(__name__)
web.register_blueprint(api)

@web.route("/example/")
def example():
    return render_template("example.html")

@web.route("/")
def home():
    return render_template("home.html", nav_section="home", section="Home")

@web.route("/hosts/")
def hosts():
    hosts = Host.query.all()

    return render_template("hosts.html", nav_section="hosts", section="Hosts",
        title="Manage Hosts", hosts=hosts)

@web.route("/hosts/add/")
def hosts_add():
    return render_template("host-form.html", nav_section="hosts",
        section="Hosts", title="Add Host", method="add")

@web.route("/hosts/edit/<host_id>/")
def hosts_edit(host_id):
    host = Host.query.get(host_id)
    if not host:
        abort(404)

    return render_template("host-form.html", nav_section="hosts",
        section="Hosts", title="Edit Host", method="edit", host=host)

@web.route("/host-groups/")
def host_groups():
    host_groups = HostGroup.query.all()

    return render_template("host-groups.html", nav_section="host-groups",
        section="Host Groups", title="Manage Host Groups",
        host_groups=host_groups)

@web.route("/host-groups/add/")
def host_groups_add():
    hosts = Host.query.all()
    host_groups = HostGroup.query.all()

    return render_template("host-group-form.html", nav_section="host-groups",
        section="Host Groups", title="Add Host Group", method="add",
        hosts=hosts, host_groups=host_groups)

@web.route("/host-groups/edit/<host_group_id>/")
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
def plugins():
    plugins = Plugin.query.all()

    return render_template("plugins.html", nav_section="plugins",
        section="Plugins", title="Manage Plugins", plugins=plugins)

@web.route("/plugins/install/")
def plugins_install():
    return render_template("plugin-form.html", nav_section="plugins",
        section="Plugins", title="Install Plugin")

@web.route("/plugins/thresholds/<plugin_id>/")
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
def scheduling():
    schedules = Schedule.query.all()

    return render_template("scheduling.html", nav_section="scheduling",
        section="Scheduling", title="Manage Schedules", schedules=schedules)

@web.route("/scheduling/add/")
def scheduling_add():
    checks = Check.query.all()

    iso_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return render_template("scheduling-form.html", nav_section="scheduling",
        section="Scheduling", title="Add Schedule", method="add",
        checks=checks, iso_datetime=iso_datetime)

@web.route("/scheduling/edit/<schedule_id>/")
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
def checks():
    checks = Check.query.all()

    return render_template("checks.html", nav_section="checks",
        section="Checks", title="Manage Checks", checks=checks)

@web.route("/checks/add/")
def checks_add():
    hosts = Host.query.all()
    host_groups = HostGroup.query.all()
    plugins = Plugin.query.all()

    return render_template("check-form.html", nav_section="checks",
        section="Checks", title="Add Check", hosts=hosts, method="add",
        host_groups=host_groups, plugins=plugins)

@web.route("/checks/edit/<check_id>/")
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
def users():
    users = User.query.all()

    return render_template("users.html", nav_section="users", section="Users",
        title="Manage Users", users=users)

@web.route("/users/add/")
def users_add():
    return render_template("user-form.html", nav_section="users",
        section="Users", title="Add User", method="add")

@web.route("/users/edit/<user_id>/")
def users_edit(user_id):
    user = User.query.get(user_id)
    if not user:
        abort(404)

    return render_template("user-form.html", nav_section="users",
        section="Users", title="Edit User", method="edit", user=user)

if __name__ == "__main__":
    web.run(debug=True)
