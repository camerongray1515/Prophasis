from flask import Flask, render_template, abort
from api import api
from models import Host, HostGroup, HostGroupAssignment, Plugin, Check,\
    CheckAssignment, CheckPlugin

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

@web.route("/scheduling/")
def scheduling():
    return render_template("scheduling.html", nav_section="scheduling",
        section="Scheduling", title="Manage Schedules")

@web.route("/scheduling/add/")
def scheduling_add():
    hosts = Host.query.all()
    groups = HostGroup.query.all()

    return render_template("scheduling-form.html", nav_section="scheduling",
        section="Scheduling", title="Add Schedule", method="add", hosts=hosts,
        groups=groups)

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

if __name__ == "__main__":
    web.run(debug=True)