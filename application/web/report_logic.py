from models import Host, PluginResult, Service

severities = {
    "critical": {"class": "danger", "display": "Critical"},
    "major": {"class": "warning", "display": "Major"},
    "minor": {"class": "info", "display": "Minor"},
    "unknown": {"class": "primary", "display": "Unknown"},
    "ok": {"class": "success", "display": "Ok"},
    "no_data": {"class": "default", "display": "No Data"},
    "degraded": {"class": "default", "display": "Degraded"}
}

def get_all_hosts():
    severity_ordering = ["critical", "major", "minor", "unknown", "ok",
        "no_data"]
        
    all_hosts = Host.query.all()

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

def get_all_services():
    severity_ordering = ["critical", "degraded", "major", "minor", "unknown", "ok",
        "no_data"]

    all_services = Service.query.all()

    categorised_services = {}
    for severity in severities.keys():
        categorised_services[severity] = []
    for service in all_services:
        service.css_class = severities[service.health]["class"]
        service.display = severities[service.health]["display"]
        categorised_services[service.health].append(service)

    ordered_services = []
    for severity in severity_ordering:
        ordered_services += categorised_services[severity]

    return ordered_services
