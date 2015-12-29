import os
import sys
import json
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime,\
    Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from datetime import datetime
from config import get_config, get_config_value
from copy import deepcopy

config = get_config()

connection_string = get_config_value(config, "db_connection_string")
def initialise():
    global engine, Session, session
    engine = create_engine(connection_string)
    Session = sessionmaker(bind=engine)
    session = scoped_session(Session)

initialise()

Base = declarative_base()
Base.query = session.query_property()

class Host(Base):
    __tablename__ = "hosts"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    host = Column(String)
    description = Column(Text)
    auth_key = Column(String)
    check_certificate = Column(Boolean, default=True)

    group_assignments = relationship("HostGroupAssignment",
        cascade="all, delete, delete-orphan", backref="host")

    check_assignments = relationship("CheckAssignment",
        cascade="all, delete, delete-orphan", backref="host")

    check_results = relationship("PluginResult",
        cascade="all, delete, delete-orphan", backref="host")

    service_dependencies = relationship("ServiceDependency",
        cascade="all, delete, delete-orphan", backref="host")

    redundancy_group_components = relationship("RedundancyGroupComponent",
        cascade="all, delete, delete-orphan", backref="host")

    # TODO: Figure out recursion for groups within groups
    @property
    def assigned_plugins(self):
        plugins = []
        all_check_assignments = []
        all_check_assignments += self.check_assignments
        for assignment in self.group_assignments:
            all_check_assignments += assignment.host_group.check_assignments

        for check_assignment in all_check_assignments:
            for check_plugin in check_assignment.check.check_plugins:
                plugins.append(check_plugin.plugin)

        # Deduplicate to be safe
        found_plugin_ids = []
        deduplicated_plugins = []
        for plugin in plugins:
            if plugin.id not in found_plugin_ids:
                found_plugin_ids.append(plugin.id)
                deduplicated_plugins.append(plugin)

        return deduplicated_plugins

    @property
    def member_of(self):
        groups = []
        for assignment in self.group_assignments:
            if assignment.host_group and assignment.host_group not in groups:
                groups.append(assignment.host_group)
                groups += Host._traverse_groups(assignment.host_group.id,
                    groups)
        return groups

    def _traverse_groups(group_id, visited_groups=None):
        groups = []
        assignments = HostGroupAssignment.query.filter(
            HostGroupAssignment.member_host_group_id == group_id)
        for assignment in assignments:
            if assignment.host_group not in visited_groups:
                groups.append(assignment.host_group)
                groups += Host._traverse_groups(assignment.host_group_id,
                    groups+visited_groups)

        return groups

    def __repr__(self):
        return "<Host id: {0}, name: {1}, host: {2}>".format(self.id,
            self.name, self.host)

class HostGroup(Base):
    __tablename__ = "host_groups"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(Text)

    check_assignments = relationship("CheckAssignment",
        cascade="all, delete, delete-orphan", backref="host_group")

    group_assignments = relationship("HostGroupAssignment",
        cascade="all, delete, delete-orphan", backref="host_group",
        foreign_keys="HostGroupAssignment.host_group_id")

    group_membership = relationship("HostGroupAssignment",
        cascade="all, delete, delete-orphan", backref="member_host_group",
        foreign_keys="HostGroupAssignment.member_host_group_id")

    service_dependencies = relationship("ServiceDependency",
        cascade="all, delete, delete-orphan", backref="host_group")

    redundancy_group_components = relationship("RedundancyGroupComponent",
        cascade="all, delete, delete-orphan", backref="host_group")

    @property
    def member_hosts(self):
        return self._get_hosts()

    def _get_hosts(self, visited_groups=None):
        if visited_groups == None:
            visited_groups = []
        hosts = []
        visited_groups.append(self.id)

        for assignment in self.group_assignments:
            if assignment.member_host_id:
                hosts.append(assignment.host)
            elif assignment.member_host_group_id:
                if assignment.member_host_group_id not in visited_groups:
                    hosts += assignment.member_host_group._get_hosts(
                        visited_groups=visited_groups)

        return hosts

    def __repr__(self):
        return "<HostGroup id: {0}, name: {1}>".format(self.id, self.name)

class HostGroupAssignment(Base):
    __tablename__ = "host_group_assignment"

    id = Column(Integer, primary_key=True)
    member_host_id = Column(Integer, ForeignKey("hosts.id"))
    member_host_group_id = Column(Integer, ForeignKey("host_groups.id"))
    host_group_id = Column(Integer, ForeignKey("host_groups.id"))

    def __repr__(self):
        return ("<HostGroupAssignment member_host_id: {0}, "
            "member_host_group_id: {1}, host_group_id: {2}>".format(
                self.member_host_id, self.member_host_group_id,
                self.host_group_id))

class PluginResult(Base):
    __tablename__ = "plugin_results"

    id = Column(Integer, primary_key=True)
    host_id = Column(Integer, ForeignKey("hosts.id"))
    plugin_id = Column(String, ForeignKey("plugins.id"))
    check_id = Column(Integer, ForeignKey("checks.id"))
    value = Column(Float)
    message = Column(String)
    result_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    health_status = Column(String)

    def __repr__(self):
        return ("<PluginResult host_id: {0}, plugin_id: {1}, timestamp: {2}"
            ">".format(self.host_id, self.plugin_id, self.timestamp))

    def to_dict(self):
        data = {
            "id": self.id,
            "host_id": self.host_id,
            "plugin_id": self.plugin_id,
            "check_id": self.check_id,
            "value": self.value,
            "message": self.message,
            "result_type": self.result_type,
            "timestamp": self.timestamp.timestamp(),
            "health_status": self.health_status
        }
        return data

class Plugin(Base):
    __tablename__ = "plugins"

    id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(Text)
    version = Column(Float)
    archive_file = Column(String)
    view = Column(String)
    view_source = Column(Text)

    check_results = relationship("PluginResult",
        cascade="all, delete, delete-orphan", backref="plugin")

    check_plugins = relationship("CheckPlugin",
        cascade="all, delete, delete-orphan", backref="plugin")

    plugin_thresholds = relationship("PluginThreshold",
        cascade="all, delete, delete-orphan", backref="plugin")

    def __repr__(self):
        return "<Plugin id: {0}, version: {1}>".format(self.id,
            self.version)

class PluginThreshold(Base):
    __tablename__ = "plugin_thresholds"

    id = Column(Integer, primary_key=True)
    plugin_id = Column(String, ForeignKey("plugins.id"))
    check_id = Column(Integer, ForeignKey("checks.id"))
    default = Column(Boolean)
    n_historical = Column(Integer) # How many previous values to fetch
    classification_code = Column(Text)

    def __repr__(self):
        return ("<PluginThreshold plugin_id: {0}, check_id: {1}, default: {2}>"
            "".format(self.plugin_id, self.check_id, self.default))

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(Text)

    intervals = relationship("ScheduleInterval",
        cascade="all, delete, delete-orphan", backref="schedule")

    schedule_checks = relationship("ScheduleCheck",
        cascade="all, delete, delete-orphan", backref="schedules")

    def __repr__(self):
        return "<Schedule id: {0}, name: {1}>".format(self.id, self.name)

class ScheduleInterval(Base):
    __tablename__ = "schedule_intervals"

    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"))
    start_timestamp = Column(DateTime)
    interval_seconds = Column(Integer)
    execute_next = Column(DateTime)
    last_executed = Column(DateTime)

    def set_interval(self, value, unit):
        if unit == "second":
            self.interval_seconds = value
        elif unit == "minute":
            self.interval_seconds = value * 60
        elif unit == "hour":
            self.interval_seconds = value * 60 * 60
        elif unit == "day":
            self.interval_seconds = value * 60 * 60 * 24
        elif unit == "week":
            self.interval_seconds = value * 60 * 60 * 24 * 7
        else:
            raise ValueError("Unit is not recognised")

    def _interval(self):
        unit_dividers = {
            "minute": 60,
            "hour": 60 * 60,
            "day": 60 * 60 * 24,
            "week": 60 * 60 * 24 * 7
        }

        previous_unit_interval = (self.interval_seconds, "second")
        for unit in ["minute", "hour", "day", "week"]:
            if self.interval_seconds % unit_dividers[unit] == 0:
                divided_value = int(
                    self.interval_seconds / unit_dividers[unit])
                previous_unit_interval = (divided_value, unit)
            else:
                return previous_unit_interval

        return (self.interval_seconds, "second")

    @property
    def interval_value(self):
        return self._interval()[0]

    @property
    def interval_unit(self):
        return self._interval()[1]

    @property
    def start_iso_datetime(self):
        return self.start_timestamp.strftime("%Y-%m-%d %H:%M:%S")


    def __repr__(self):
        return ("<ScheduleInterval schedule_id: {0}, start_timestamp: {1},"
            " interval_seconds: {2}>".format(self.schedule_id,
                self.start_timestamp, self.interval_seconds))

class Check(Base):
    __tablename__ = "checks"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(Text)

    def flatten(self):
        """
            Returns tuples of (host, plugin) for every entry in the check
        """
        flattened = []
        for assignment in self.check_assignments:
            hosts = []
            if assignment.host:
                hosts = [assignment.host]
            else:
                hosts = assignment.host_group.member_hosts

            for host in hosts:
                for check_plugin in self.check_plugins:
                    flattened.append((host, check_plugin.plugin))

        return flattened

    check_assignments = relationship("CheckAssignment",
        cascade="all, delete, delete-orphan", backref="check")

    check_plugins = relationship("CheckPlugin",
        cascade="all, delete, delete-orphan", backref="check")

    schedule_checks = relationship("ScheduleCheck",
        cascade="all, delete, delete-orphan", backref="check")

    plugin_thresholds = relationship("PluginThreshold",
        cascade="all, delete, delete-orphan", backref="check")

    plugin_results = relationship("PluginResult",
        cascade="all, delete, delete-orphan", backref="check")

    def __repr__(self):
        return ("<Check id: {0}, name: {1}>".format(self.id, self.name))

class CheckPlugin(Base):
    __tablename__ = "check_plugins"

    id = Column(Integer, primary_key=True)
    check_id = Column(Integer, ForeignKey("checks.id"))
    plugin_id = Column(String, ForeignKey("plugins.id"))

    def __repr__(self):
        return ("<CheckPlugin check_id: {0}, plugin_id: {1}>".format(
            self.check_id, self.plugin_id))

class CheckAssignment(Base):
    __tablename__ = "check_assignments"

    id = Column(Integer, primary_key=True)
    check_id = Column(Integer, ForeignKey("checks.id"))
    host_id = Column(Integer, ForeignKey("hosts.id"))
    host_group_id = Column(Integer, ForeignKey("host_groups.id"))

    def __repr__(self):
        return ("<CheckAssignment check_id: {0}, host_id: {1}, "
            "host_group_id: {2}>".format(self.check_id, self.host_id,
            self.host_group_id))

class ScheduleCheck(Base):
    __tablename__ = "schedule_checks"

    id = Column(Integer, primary_key=True)
    check_id = Column(Integer, ForeignKey("checks.id"))
    schedule_id = Column(Integer, ForeignKey("schedules.id"))

    def __repr__(self):
        return ("<ScheduleCheck check_id: {0}, schedule_id: {1}>".format(
            self.check_id, self.schedule_id))

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    password_hash = Column(String)
    email = Column(String)

    # Methods requred by flask-login
    def get_id(self):
        return str(self.id)

    def is_anonymous(self):
        return False

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def __repr__(self):
        return "<User id: {}, username: {}>".format(self.id, self.username)

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(Text)

    service_dependencies = relationship("ServiceDependency",
        cascade="all, delete, delete-orphan", backref="service")

    redundancy_groups = relationship("RedundancyGroup",
        cascade="all, delete, delete-orphan", backref="service")

    def __repr__(self):
        return "<Service id: {}, name: {}>".format(self.id, self.name)

class ServiceDependency(Base):
    __tablename__ = "service_dependencies"

    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id"))
    host_id = Column(Integer, ForeignKey("hosts.id"))
    host_group_id = Column(Integer, ForeignKey("host_groups.id"))
    redundancy_group_id = Column(Integer, ForeignKey("redundancy_groups.id"))

    def __repr__(self):
        return "<ServiceDependency id: {}>".format(self.id)

class RedundancyGroup(Base):
    __tablename__ = "redundancy_groups"

    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id"))

    service_dependencies = relationship("ServiceDependency",
        cascade="all, delete, delete-orphan", backref="redundancy_group")

    redundancy_group_components = relationship("RedundancyGroupComponent",
        cascade="all, delete, delete-orphan", backref="redundancy_group")

    def __repr__(self):
        return "<RedundancyGroup id: {}>".format(self.id)

class RedundancyGroupComponent(Base):
    __tablename__ = "redundancy_group_components"

    id = Column(Integer, primary_key=True)
    host_id = Column(Integer, ForeignKey("hosts.id"))
    host_group_id = Column(Integer, ForeignKey("host_groups.id"))
    redundancy_group_id = Column(Integer, ForeignKey("redundancy_groups.id"))

    def __repr__(self):
        return "<RedundancyGroupComponent id: {}>".format(self.id)

def create_all():
    Base.metadata.create_all(engine)

def drop_all():
    Base.metadata.drop_all(engine)

def test():
    g = HostGroup.query.get(4)
    print(g.get_hosts())
