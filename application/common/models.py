from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime,\
    Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from datetime import datetime

# TODO: Move this into some sort of file
connection_string = "sqlite:///db.sqlite"
engine = create_engine(connection_string)
Session = sessionmaker(bind=engine)
session = scoped_session(Session)

Base = declarative_base()
Base.query = session.query_property()

class Host(Base):
    __tablename__ = "hosts"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    host = Column(String)
    description = Column(Text)
    auth_key = Column(String)

    group_assignments = relationship("HostGroupAssignment",
        cascade="all, delete, delete-orphan", backref="host")

    check_assignments = relationship("CheckAssignment",
        cascade="all, delete, delete-orphan", backref="host")

    check_results = relationship("PluginResult",
        cascade="all, delete, delete-orphan", backref="host")

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
    value = Column(String)
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return ("<PluginResult host_id: {0}, plugin_id: {1}, timestamp: {2}"
            ">".format(self.host_id, self.plugin_id, self.timestamp))

class Plugin(Base):
    __tablename__ = "plugins"

    id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(Text)
    version = Column(Float)
    archive_file = Column(String)

    check_results = relationship("PluginResult",
        cascade="all, delete, delete-orphan", backref="plugin")

    check_plugins = relationship("CheckPlugin",
        cascade="all, delete, delete-orphan", backref="plugin")

    def __repr__(self):
        return "<Plugin id: {0}, version: {1}>".format(self.id,
            self.version)

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    all_hosts = Column(Boolean)
    all_plugins = Column(Boolean)

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

    def __repr__(self):
        return ("<ScheduleInterval schedule_id: {0}, start_timestamp: {1},"
            " interval_seconds: {2}>".format(self.schedule_id,
                self.start_timestamp, self.interval_seconds))

class Check(Base):
    __tablename__ = "checks"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(Text)

    check_assignments = relationship("CheckAssignment",
        cascade="all, delete, delete-orphan", backref="check")

    check_plugins = relationship("CheckPlugin",
        cascade="all, delete, delete-orphan", backref="check")

    schedule_checks = relationship("ScheduleCheck",
        cascade="all, delete, delete-orphan", backref="check")

    def __repr__(self):
        return ("<Check id: {0}, name: {1}>".format(self.id, self.name))

class CheckPlugin(Base):
    __tablename__ = "check_plugins"

    id = Column(Integer, primary_key=True)
    check_id = Column(Integer, ForeignKey("checks.id"))
    plugin_id = Column(Integer, ForeignKey("plugins.id"))

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

def create_all():
    Base.metadata.create_all(engine)

def test():
    g = HostGroup.query.get(4)
    print(g.get_hosts())