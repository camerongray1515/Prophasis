from multiprocessing import Process, Queue
import time
from datetime import datetime

host_queues = {}

def runner(queue, host):
    while not queue.empty():
        plugin = queue.get()
        # This is where the request will be made to the agent
        print("{0}: Executing {1} on {2}".format(datetime.utcnow(), plugin.name, host.name))
        time.sleep(1)
        print("{0}: Completed {1} on {2}".format(datetime.utcnow(), plugin.name, host.name))
    # print("Killing runner for {0}".format(host.name))

def dispatch_job(host, plugin):
    if host.id not in host_queues:
        host_queues[host.id] = {
            "process": None,
            "queue": Queue()
        }

    host_queues[host.id]["queue"].put(plugin)
    if not host_queues[host.id]["process"] or \
        not host_queues[host.id]["process"].is_alive():
        host_queues[host.id]["process"] = Process(target=runner, args=(
            host_queues[host.id]["queue"], host
        ))
        host_queues[host.id]["process"].start()

    return host_queues[host.id]["queue"].qsize()
