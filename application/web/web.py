from flask import Flask, render_template, abort
from api import api
from models import Host, HostGroup, HostGroupAssignment, Plugin

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

if __name__ == "__main__":
    web.run(debug=True)
