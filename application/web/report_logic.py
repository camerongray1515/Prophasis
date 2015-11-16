from models import Host, PluginResult

def get_all_hosts():
    severity_ordering = ["critical", "major", "minor", "unknown", "ok",
        "no_data"]
    severities = {
        "critical": {
            "priority": 5,
            "class": "danger",
            "display": "Critical"
            },
        "major": {
            "priority": 4,
            "class": "warning",
            "display": "Major"
            },
        "minor": {
            "priority": 3,
            "class": "info",
            "display": "Minor"
            },
        "unknown": {
            "priority": 2,
            "class": "primary",
            "display": "Unknown"
            },
        "ok": {
            "priority": 1,
            "class": "success",
            "display": "Ok"
            },
        "no_data": {
            "priority": 0,
            "class": "default",
            "display": "No Data"
            }
    }
    all_hosts = Host.query.all()

    # For each host find the most severe result from the assigned plugins and
    # take that as the health of the entire node
    categorised_hosts = {}
    for severity in severities.keys():
        categorised_hosts[severity] = []
    for host in all_hosts:
        health = "no_data"
        highest_severity = 0
        for plugin in host.assigned_plugins:
            results = PluginResult.query.filter(
                PluginResult.plugin_id == plugin.id).filter(
                    PluginResult.host_id == host.id).order_by(
                PluginResult.id.desc()).all()
            if results:
                result = results[0]
                if severities[result.health_status]["priority"] >\
                    highest_severity:
                    health = result.health_status
                    highest_severity = severities[result.health_status]\
                        ["priority"]
        host.health = health
        host.css_class = severities[health]["class"]
        host.display = severities[health]["display"]
        categorised_hosts[health].append(host)

    # Now order hosts by their severities
    ordered_hosts = []
    for severity in severity_ordering:
        ordered_hosts += categorised_hosts[severity]

    return ordered_hosts
