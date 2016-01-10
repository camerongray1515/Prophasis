from models import Host, PluginResult

def get_all_hosts():
    severity_ordering = ["critical", "major", "minor", "unknown", "ok",
        "no_data"]
    severities = {
        "critical": {"class": "danger", "display": "Critical"},
        "major": {"class": "warning", "display": "Major"},
        "minor": {"class": "info", "display": "Minor"},
        "unknown": {"class": "primary", "display": "Unknown"},
        "ok": {"class": "success", "display": "Ok"},
        "no_data": {"class": "default", "display": "No Data"}
    }
    all_hosts = Host.query.all()

    # For each host find the most severe result from the assigned plugins and
    # take that as the health of the entire node
    categorised_hosts = {}
    for severity in severities.keys():
        categorised_hosts[severity] = []
    for host in all_hosts:
        host.css_class = severities[host.health]["class"]
        host.display = severities[host.health]["display"]
        categorised_hosts[host.health].append(host)

    # Now order hosts by their severities
    ordered_hosts = []
    for severity in severity_ordering:
        ordered_hosts += categorised_hosts[severity]

    return ordered_hosts
