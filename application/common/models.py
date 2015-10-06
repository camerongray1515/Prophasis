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

    check_results = relationship("CheckResult",
        cascade="all, delete, delete-orphan", backref="host")

    plugin_assignments = relationship("PluginAssignment",
        cascade="all, delete, delete-orphan", backref="host")

    schedule_host_assignments = relationship("ScheduleHostAssignment",
        cascade="all, delete, delete-orphan", backref="host")

    def __repr__(self):
        return "<Host id: {0}, name: {1}, host: {2}>".format(self.id,
            self.name, self.host)

class HostGroup(Base):
    __tablename__ = "host_groups"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(Text)

    group_assignments = relationship("HostGroupAssignment",
        cascade="all, delete, delete-orphan", backref="host_group")

    plugin_assignments = relationship("PluginAssignment",
        cascade="all, delete, delete-orphan", backref="host_group")

    def __repr__(self):
        return "<HostGroup id: {0}, name: {1}>".format(self.id, self.name)

class HostGroupAssignment(Base):
    __tablename__ = "host_group_assignment"

    id = Column(Integer, primary_key=True)
    host_id = Column(Integer, ForeignKey("hosts.id"))
    host_group_id = Column(Integer, ForeignKey("host_groups.id"))

    def __repr__(self):
        return "<HostGroupAssignment host_id: {0}, host_group_id: {1}>"\
            .format(self.host_id, self.host_group_id)

class CheckResult(Base):
    __tablename__ = "check_results"

    id = Column(Integer, primary_key=True)
    host_id = Column(Integer, ForeignKey("hosts.id"))
    plugin_id = Column(String, ForeignKey("plugins.id"))
    value = Column(String)
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return ("<CheckResult host_id: {0}, plugin_id: {1}, timestamp: {2}"
            ">".format(self.host_id, self.plugin_id, self.timestamp))

class PluginAssignment(Base):
    __tablename__ = "plugin_assignment"

    id = Column(Integer, primary_key=True)
    plugin_id = Column(String, ForeignKey("plugins.id"))
    host_id = Column(Integer, ForeignKey("hosts.id"))
    host_group_id = Column(Integer, ForeignKey("host_groups.id"))

    def __repr__(self):
        return ("<PluginAssignment plugin_id: {0}, host_id: {1}, "
            "host_group_id: {2}>".format(self.plugin_id, self.host_id,
                self.host_group_id))

class SchedulePluginAssignment(Base):
    __tablename__ = "schedule_plugin_assignments"

    id = Column(Integer, primary_key=True)
    plugin_id = Column(String, ForeignKey("plugins.id"))
    schedule_id = Column(Integer, ForeignKey("schedules.id"))

    def __repr__(self):
        return ("<SchedulePluginAssignment plugin_id: {0}, schedule_id: "
            "{1}>".format(self.plugin_id, self.schedule_id))

class ScheduleHostAssignment(Base):
    __tablename__ = "schedule_host_assignments"

    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"))
    host_id = Column(Integer, ForeignKey("hosts.id"))

    def __repr__(self):
        return "<ScheduleHostAssignment schedule_id: {0}, host_id: {1}"\
        .format(self.schedule_id, self.host_id)

class Plugin(Base):
    __tablename__ = "plugins"

    id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(Text)
    version = Column(Float)
    archive_file = Column(String)

    check_results = relationship("CheckResult",
        cascade="all, delete, delete-orphan", backref="plugin")

    plugin_assignments = relationship("PluginAssignment",
        cascade="all, delete, delete-orphan", backref="plugin")

    schedule_plugin_assignments = relationship("SchedulePluginAssignment",
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

    host_assignments = relationship("ScheduleHostAssignment",
        cascade="all, delete, delete-orphan", backref="schedule")

    plugin_assignments = relationship("SchedulePluginAssignment",
        cascade="all, delete, delete-orphan", backref="schedule")

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
        
def create_all():
    Base.metadata.create_all(engine)
