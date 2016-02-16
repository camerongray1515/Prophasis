import time
from datetime import datetime, timedelta
from prophasis_common.models import session, ScheduleInterval
from sqlalchemy import or_
from .config import get_config, get_config_value

config = get_config()
scheduler_delay = get_config_value(config, "scheduler_delay")
lateness_delta = timedelta(0, get_config_value(config, "max_lateness"))

def scheduler_loop(callback):
    while True:
        current_timestamp = datetime.now()

        intervals = ScheduleInterval.query.filter(
            ScheduleInterval.execute_next == None)
        for i in intervals:
            i.execute_next = current_timestamp
            (num_iterations, execute_next) = walk_execute_next(i.execute_next,
                i.interval_seconds, current_timestamp)

        session.commit()

        intervals = ScheduleInterval.query.filter(
            ScheduleInterval.execute_next < current_timestamp).filter(or_(
                ScheduleInterval.last_executed < ScheduleInterval.execute_next,
                ScheduleInterval.last_executed == None
            ))

        for i in intervals:
            # Only execute if it is not too late, however still walk the
            # timestamp, otherwise late schedules will never execute again!
            if i.execute_next >= current_timestamp - lateness_delta:
                callback(i.schedule)

            (num_iterations, execute_next) = walk_execute_next(i.execute_next,
                i.interval_seconds, current_timestamp)
            i.execute_next = execute_next
            i.last_executed = current_timestamp

        session.commit()

        time.sleep(scheduler_delay)

def walk_execute_next(execute_next, interval_seconds, current_timestamp):
    interval_delta = timedelta(0, interval_seconds)
    num_iterations = 0
    while execute_next < current_timestamp:
        execute_next += interval_delta
        num_iterations += 1
    return (num_iterations, execute_next)

if __name__ == "__main__":
    scheduler_loop()
