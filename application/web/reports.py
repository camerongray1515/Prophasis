import report_logic
from flask import Blueprint, request, render_template
from flask.ext.login import login_required
from models import PluginResult

reports = Blueprint("reports", __name__, url_prefix="/reports")

@reports.route("/hosts/")
def hosts():
    ordered_hosts = report_logic.get_all_hosts()

    return render_template("host-health.html", nav_section="reports/hosts",
        section="Hosts", ordered_hosts=ordered_hosts)

@reports.route("/hosts/<host_id>/")
def hosts_host_id(host_id):
    check_plugin_views = {}
    results = PluginResult.query.filter(PluginResult.host_id == host_id)
    # Separate results by check and plugin
    for result in results:
        check_name = result.check.name
        plugin_name = result.plugin.name
        if check_name not in check_plugin_views:
            check_plugin_views[check_name] = {}
        if plugin_name not in check_plugin_views[check_name]:
            check_plugin_views[check_name][plugin_name] = {
                "check": result.check, "plugin": result.plugin, "results": []}

        check_plugin_views[check_name][plugin_name]["results"].append(
            result.to_dict())

    rendered_views = {}
    for check_name in check_plugin_views.keys():
        for plugin_name in check_plugin_views[check_name].keys():
            entry = check_plugin_views[check_name][plugin_name]
            view_name = entry["plugin"].view
            if view_name != "custom":
                rendered_view = render_template("views/{}.html".format(
                    view_name), results=entry["results"])

                if check_name not in rendered_views:
                    rendered_views[check_name] = []

                rendered_views[check_name].append({
                    "plugin_name": plugin_name,
                    "rendered_view": rendered_view
                });

    return render_template("host-views.html", views=rendered_views)
