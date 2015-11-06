import report_logic
from flask import Blueprint, request, render_template
from flask.ext.login import login_required

reports = Blueprint("reports", __name__, url_prefix="/reports")

@reports.route("/hosts/")
def hosts():
    ordered_hosts = report_logic.get_all_hosts()

    return render_template("host-health.html", nav_section="reports/hosts",
        section="Hosts", ordered_hosts=ordered_hosts)
