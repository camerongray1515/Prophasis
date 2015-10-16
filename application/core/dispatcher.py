from multiprocessing import Process, Queue
import time

host_queues = {}

def runner(queue, host):
    while not queue.empty():
        plugin = queue.get()
        # This is where the request will be made to the agent
        print("Executing {0} on {1}".format(plugin.name, host.name))
        time.sleep(1)
        print("Completed {0} on {1}".format(plugin.name, host.name))
    print("Killing runner for {0}".format(host.name))

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
