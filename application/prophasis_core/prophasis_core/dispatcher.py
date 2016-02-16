import os
import multiprocessing
# from multiprocessing import Process, Queue
from .agent_api import Agent, CommandUnsuccessfulError, AuthenticationError, \
    RequestError
from requests.exceptions import ConnectionError, Timeout
from .config import get_config, get_config_value
from prophasis_common.models import PluginResult, session, Host
from datetime import datetime
from .classification import classify
from prophasis_common.alerting import process_alerts

host_queues = {}
config = get_config()

ctx = multiprocessing.get_context("spawn")
Process = ctx.Process
Queue = ctx.Queue

def runner(queue, host):
    while not queue.empty():
        plugin, check_id = queue.get()
        perform_check(host, plugin, check_id)

def perform_check(host, plugin, check_id):
    a = Agent(host.host, host.auth_key, verify_certs=host.check_certificate)
    error = None
    result_type = "plugin"
    try:
        update_required = a.check_plugin_verison(plugin.id, plugin.version)
        if update_required:
            plugin_file = os.path.join(get_config_value(config, "plugin_repo"),
                plugin.archive_file)
            with open(plugin_file, "rb") as f:
                a.update_plugin(plugin.id, f)
        (value, message) = a.get_plugin_data(plugin.id)
    except CommandUnsuccessfulError as e:
        error = str(e)
        result_type = "command_unsuccessful"
    except AuthenticationError as e:
        error = str(e)
        result_type = "authentication_error"
    except RequestError as e:
        error = str(e)
        result_type = "request_error"
    except ConnectionError as e:
        error = str(e)
        result_type = "connection_error"
    except Timeout as e:
        error = str(e)
        result_type = "connection_timeout"

    if error:
        message = error
        value = None

    old_health = Host.query.get(host.id).health

    pr = PluginResult(host_id=host.id, plugin_id=plugin.id, check_id=check_id,
        value=value, message=message, result_type=result_type,
        timestamp=datetime.now())

    pr.health_status = classify(pr, check_id)
    session.add(pr)
    session.commit()

    new_health = Host.query.get(host.id).health
    process_alerts(host.id, plugin.id, check_id, old_health, new_health)


def dispatch_job(host, plugin, check_id):
    if host.id not in host_queues:
        host_queues[host.id] = {
            "process": None,
            "queue": Queue()
        }

    host_queues[host.id]["queue"].put((plugin, check_id))
    if not host_queues[host.id]["process"] or \
        not host_queues[host.id]["process"].is_alive():
        host_queues[host.id]["process"] = Process(target=runner, args=(
            host_queues[host.id]["queue"], host
        ))
        host_queues[host.id]["process"].start()

    return host_queues[host.id]["queue"].qsize()
