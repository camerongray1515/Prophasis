from .scheduler import scheduler_loop
from .dispatcher import dispatch_job

def schedule_callback(schedule):
    for schedule_check in schedule.schedule_checks:
        for host, plugin in schedule_check.check.flatten():
            qsize = dispatch_job(host, plugin, schedule_check.check_id)
            # print("{0} items in queue".format(qsize))

def main():
    print("Core starting up...")

    print("Starting scheduler")
    scheduler_loop(callback=schedule_callback)

if __name__ == "__main__":
    main()
