import report_logic
import uuid
import datetime
import json
from flask import Blueprint, request, render_template, session
from flask.ext.login import login_required
from models import PluginResult
from jinja2 import Template

reports = Blueprint("reports", __name__, url_prefix="/reports")

@reports.route("/hosts/")
@login_required
def hosts():
    ordered_hosts = report_logic.get_all_hosts()

    return render_template("host-health.html", nav_section="reports/hosts",
        section="Hosts", title="Host Health", ordered_hosts=ordered_hosts)

@reports.route("/hosts/<host_id>/", methods=["GET", "POST"])
@login_required
def hosts_host_id(host_id):
    if request.form.get("end-timestamp"):
        end_timestamp = request.form.get("end-timestamp")
    else:
        end_timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    unit_dividers = {
        "minute": 60,
        "hour": 60 * 60,
        "day": 60 * 60 * 24,
        "week": 60 * 60 * 24 * 7
    }

    if request.form.get("historical-unit"):
        unit = request.form.get("historical-unit")
        value = request.form.get("historical-unit-value")
        session["seconds_historical"] = int(value) * unit_dividers[unit]

    if "seconds_historical" not in session:
        session["seconds_historical"] = 60*60 # Last hour of data

    unit_divider_ordering = ["minute", "hour", "day", "week"]

    historical_unit_value = session["seconds_historical"]
    historical_unit = "second"
    for unit in unit_divider_ordering:
        if session["seconds_historical"] % unit_dividers[unit] == 0:
            historical_unit = unit
            historical_unit_value = int(session["seconds_historical"] / \
                unit_dividers[unit])

    end_time = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%S")
    start_time = end_time - datetime.timedelta(0, session["seconds_historical"])
    check_plugin_views = {}
    results = PluginResult.query.filter(PluginResult.host_id == host_id).filter(
        PluginResult.timestamp >= start_time).filter(
            PluginResult.timestamp <= end_time).order_by(PluginResult.timestamp)
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

            if view_name == "custom":
                template = Template(entry["plugin"].view_source)
                rendered_view = template.render(results=entry["results"],
                    identifier=uuid.uuid4(),
                    results_json=json.dumps(entry["results"]))
            else:
                rendered_view = render_template("views/{}.html".format(
                    view_name), results=entry["results"],
                        identifier=uuid.uuid4(),
                        results_json=json.dumps(entry["results"]))

            if check_name not in rendered_views:
                rendered_views[check_name] = []

            rendered_views[check_name].append({
                "name": plugin_name,
                "rendered_view": rendered_view
            });

    return render_template("host-views.html", nav_section="reports/hosts",
        section="Hosts", title="Host Information", views=rendered_views,
        end_timestamp=end_timestamp,
        historical_unit_value=historical_unit_value,
        historical_unit=historical_unit)
