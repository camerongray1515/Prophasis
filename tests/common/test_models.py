import unittest
import os
os.environ["UNDER_TEST"] = "1"
from prophasis_common.models import create_all, drop_all, session, Host,\
    HostGroup, HostGroupAssignment, Plugin, PluginResult, Service,\
    ServiceDependency, RedundancyGroup, RedundancyGroupComponent, Alert,\
    AlertCheckEntity, Check, AlertRestrictToEntity

class TestGetHostMembersip(unittest.TestCase):
    def setUp(self):
        session.commit()
        drop_all()
        create_all()

        # Add Hosts
        for i in range(1,5):
            session.add(Host(id=i, name="Host {}".format(i)))

        # Add Groups
        for i in range(1,9):
            session.add(HostGroup(id=i, name="Group {}".format(i)))

        session.flush()

        # Assign hosts to groups
        session.add(HostGroupAssignment(member_host_id=1, host_group_id=1))
        session.add(HostGroupAssignment(member_host_id=1, host_group_id=2))
        session.add(HostGroupAssignment(member_host_id=2, host_group_id=1))
        session.add(HostGroupAssignment(member_host_id=2, host_group_id=2))
        session.add(HostGroupAssignment(member_host_id=2, host_group_id=3))
        session.add(HostGroupAssignment(member_host_id=3, host_group_id=2))
        session.add(HostGroupAssignment(member_host_id=3, host_group_id=3))
        session.add(HostGroupAssignment(member_host_id=3, host_group_id=5))
        session.add(HostGroupAssignment(member_host_id=4, host_group_id=2))
        session.add(HostGroupAssignment(member_host_id=4, host_group_id=6))
        session.add(HostGroupAssignment(member_host_id=4, host_group_id=5))

        # Assign groups to groups
        session.add(HostGroupAssignment(member_host_group_id=4,
            host_group_id=5))
        session.add(HostGroupAssignment(member_host_group_id=3,
            host_group_id=4))
        session.add(HostGroupAssignment(member_host_group_id=6,
            host_group_id=7))
        session.add(HostGroupAssignment(member_host_group_id=7,
            host_group_id=8))
        session.add(HostGroupAssignment(member_host_group_id=8,
            host_group_id=6))

        session.commit()

    def test_no_recursion(self):
        groups = Host.query.get(1).member_of
        group_ids = []
        for group in groups:
            group_ids.append(group.id)

        self.assertEqual(sorted(group_ids), [1,2])

    def test_recursion(self):
        groups = Host.query.get(2).member_of
        group_ids = []
        for group in groups:
            group_ids.append(group.id)

        self.assertEqual(sorted(group_ids), [1,2,3,4,5])

    def test_deduplication(self):
        groups = Host.query.get(3).member_of
        group_ids = []
        for group in groups:
            group_ids.append(group.id)

        self.assertEqual(sorted(group_ids), [2,3,4,5])

    def test_cycle(self):
        groups = Host.query.get(4).member_of
        group_ids = []
        for group in groups:
            group_ids.append(group.id)

        self.assertEqual(sorted(group_ids), [2,5,6,7,8])

class TestGetHostHeatlh(unittest.TestCase):
    def setUp(self):
        session.commit()
        drop_all()
        create_all()
        # Insert all plugins
        for letter in ["A", "B", "C"]:
            session.add(Plugin(id=letter, name=letter))

        # Insert all hosts
        for number in range(1,9):
            session.add(Host(name=number))

        # Mock the assigned_plugins method
        Host.assigned_plugins = property(lambda s: Plugin.query.all())

        # All plugins OK
        session.add(PluginResult(host_id=1, plugin_id="A",
            health_status="ok"))
        session.add(PluginResult(host_id=1, plugin_id="B",
            health_status="ok"))
        session.add(PluginResult(host_id=1, plugin_id="C",
            health_status="ok"))

        # All plugins critical
        session.add(PluginResult(host_id=2, plugin_id="A",
            health_status="critical"))
        session.add(PluginResult(host_id=2, plugin_id="B",
            health_status="critical"))
        session.add(PluginResult(host_id=2, plugin_id="C",
            health_status="critical"))

        # All plugins unknown
        session.add(PluginResult(host_id=3, plugin_id="A",
            health_status="unknown"))
        session.add(PluginResult(host_id=3, plugin_id="B",
            health_status="unknown"))
        session.add(PluginResult(host_id=3, plugin_id="C",
            health_status="unknown"))

        # One plugin critical
        session.add(PluginResult(host_id=4, plugin_id="A",
            health_status="ok"))
        session.add(PluginResult(host_id=4, plugin_id="B",
            health_status="critical"))
        session.add(PluginResult(host_id=4, plugin_id="C",
            health_status="ok"))

        # One plugin unknown
        session.add(PluginResult(host_id=5, plugin_id="A",
            health_status="ok"))
        session.add(PluginResult(host_id=5, plugin_id="B",
            health_status="ok"))
        session.add(PluginResult(host_id=5, plugin_id="C",
            health_status="unknown"))

        # All plugins no_data (Host 6)

        # One plugin no data
        session.add(PluginResult(host_id=7, plugin_id="A",
            health_status="ok"))
        session.add(PluginResult(host_id=7, plugin_id="C",
            health_status="minor"))

        # Mixed results
        session.add(PluginResult(host_id=8, plugin_id="A",
            health_status="ok"))
        session.add(PluginResult(host_id=8, plugin_id="B",
            health_status="major"))
        session.add(PluginResult(host_id=8, plugin_id="C",
            health_status="minor"))

        session.commit()

    def test_all_ok(self):
        self.assertEqual(Host.query.get(1).health, "ok")

    def test_all_critical(self):
        self.assertEqual(Host.query.get(2).health, "critical")

    def test_all_unknown(self):
        self.assertEqual(Host.query.get(3).health, "unknown")

    def test_one_critical(self):
        self.assertEqual(Host.query.get(4).health, "critical")

    def test_one_unknown(self):
        self.assertEqual(Host.query.get(5).health, "unknown")

    def test_all_no_data(self):
        self.assertEqual(Host.query.get(6).health, "no_data")

    def test_one_no_data(self):
        self.assertEqual(Host.query.get(7).health, "minor")

    def test_mixed_results(self):
        self.assertEqual(Host.query.get(8).health, "major")

class TestHostAlerts(unittest.TestCase):
    def setUp(self):
        session.commit()
        drop_all()
        create_all()

        session.add(Host(id=1)) # Contains alerts 1,2,4
        session.add(Host(id=2)) # Contains alert 6,7

        for i in range(1,8):
            session.add(Alert(id=i, name=i))

        session.add(HostGroup(id=1))
        session.add(HostGroup(id=2))
        session.add(HostGroupAssignment(member_host_id=1, host_group_id=1))

        session.add(Service(id=1))
        session.add(Service(id=2))
        session.add(Service(id=3))
        session.add(ServiceDependency(host_id=1, service_id=1))
        session.add(RedundancyGroup(id=1, service_id=3))
        session.add(RedundancyGroupComponent(host_id=2, redundancy_group_id=1))
        session.add(ServiceDependency(redundancy_group_id=1, service_id=3))

        session.add(AlertCheckEntity(host_id=1, alert_id=1))
        session.add(AlertCheckEntity(host_group_id=1, alert_id=2))
        session.add(AlertCheckEntity(host_group_id=2, alert_id=3))
        session.add(AlertCheckEntity(service_id=1, alert_id=4))
        session.add(AlertCheckEntity(service_id=2, alert_id=5))
        session.add(AlertCheckEntity(host_id=2, alert_id=6))
        session.add(AlertCheckEntity(service_id=3, alert_id=7))

        session.commit()

    def test_without_redundancy_group(self):
        alert_ids = []
        for alert in Host.query.get(1).alerts:
            alert_ids.append(alert.id)
        self.assertEqual(sorted(alert_ids), [1,2,4])

    def test_with_redundancy_group(self):
        alert_ids = []
        for alert in Host.query.get(2).alerts:
            alert_ids.append(alert.id)
        self.assertEqual(sorted(alert_ids), [6,7])

class TestService(unittest.TestCase):
    def setUp(self):
        session.commit()
        drop_all()
        create_all()
        session.add(Plugin(id="Plugin", name="Plugin"))

        # Insert all hosts
        for number in range(1,7):
            session.add(Host(name=number))

        # Mock the assigned_plugins method
        Host.assigned_plugins = property(lambda s: Plugin.query.all())

        session.add(PluginResult(host_id=1, plugin_id="Plugin",
            health_status="ok"))
        session.add(PluginResult(host_id=2, plugin_id="Plugin",
            health_status="minor"))
        session.add(PluginResult(host_id=3, plugin_id="Plugin",
            health_status="major"))
        session.add(PluginResult(host_id=4, plugin_id="Plugin",
            health_status="critical"))
        session.add(PluginResult(host_id=5, plugin_id="Plugin",
            health_status="unknown"))
        # Host ID 6 has no data

        session.add(HostGroup(id=1))
        session.add(HostGroupAssignment(host_group_id=1, member_host_id=1))
        session.add(HostGroupAssignment(host_group_id=1, member_host_id=4))

        for number in range(1,11):
            session.add(Service(id=number, name=number))

        # test_failed_dependency
        session.add(ServiceDependency(service_id=1, host_id=1))
        session.add(ServiceDependency(service_id=1, host_id=1))
        session.add(ServiceDependency(service_id=1, host_id=3))

        # test_ok_dependency
        session.add(ServiceDependency(service_id=2, host_id=1))
        session.add(ServiceDependency(service_id=2, host_id=1))
        session.add(ServiceDependency(service_id=2, host_id=1))

        # test_failure_in_redundancy_group
        session.add(RedundancyGroup(id=1, service_id=3))
        session.add(RedundancyGroupComponent(redundancy_group_id=1, host_id=1))
        session.add(RedundancyGroupComponent(redundancy_group_id=1, host_id=1))
        session.add(RedundancyGroupComponent(redundancy_group_id=1, host_id=4))
        session.add(ServiceDependency(service_id=3, redundancy_group_id=1))

        # test_failed_redundancy_group
        session.add(RedundancyGroup(id=2, service_id=4))
        session.add(RedundancyGroupComponent(redundancy_group_id=2, host_id=2))
        session.add(RedundancyGroupComponent(redundancy_group_id=2, host_id=2))
        session.add(RedundancyGroupComponent(redundancy_group_id=2, host_id=4))
        session.add(ServiceDependency(service_id=4, redundancy_group_id=2))

        # redundancy_group_ok
        session.add(RedundancyGroup(id=3, service_id=5))
        session.add(RedundancyGroupComponent(redundancy_group_id=3, host_id=1))
        session.add(RedundancyGroupComponent(redundancy_group_id=3, host_id=1))
        session.add(RedundancyGroupComponent(redundancy_group_id=3, host_id=1))
        session.add(ServiceDependency(service_id=5, redundancy_group_id=3))

        # test_failed_dependency_with_redundancy_group
        session.add(RedundancyGroup(id=4, service_id=6))
        session.add(RedundancyGroupComponent(redundancy_group_id=4, host_id=1))
        session.add(RedundancyGroupComponent(redundancy_group_id=4, host_id=1))
        session.add(RedundancyGroupComponent(redundancy_group_id=4, host_id=1))
        session.add(ServiceDependency(service_id=6, redundancy_group_id=4))
        session.add(ServiceDependency(service_id=6, host_id=3))

        # test_all_dependency_failed
        session.add(ServiceDependency(service_id=7, host_id=3))
        session.add(ServiceDependency(service_id=7, host_id=3))
        session.add(ServiceDependency(service_id=7, host_id=4))

        # test_no_data
        session.add(ServiceDependency(service_id=8, host_id=1))
        session.add(ServiceDependency(service_id=8, host_id=1))
        session.add(ServiceDependency(service_id=8, host_id=6))

        # test_host_group_dependency
        session.add(ServiceDependency(service_id=9, host_group_id=1))

        # test_host_group_redundancy
        session.add(RedundancyGroup(id=5, service_id=10))
        session.add(RedundancyGroupComponent(redundancy_group_id=5,
            host_group_id=1))
        session.add(ServiceDependency(service_id=10, redundancy_group_id=5))

        session.commit()

    # One dependency has failed, rest ok - Service 1
    def test_failed_dependency(self):
        self.assertEqual(Service.query.get(1).health, "major")

    # All dependencies are ok - Service 2
    def test_ok_dependency(self):
        self.assertEqual(Service.query.get(2).health, "ok")

    # Host in redundancy group has failed, still contains ok host - Service 3
    def test_failure_in_redundancy_group(self):
        self.assertEqual(Service.query.get(3).health, "degraded")

    # Multiple hosts in redundancy groups have failed - Service 4
    def test_failed_redundancy_group(self):
        self.assertEqual(Service.query.get(4).health, "minor")

    # Redundancy group with all hosts ok - Service 5
    def redundancy_group_ok(self):
        self.assertEqual(Service.query.get(5).health, "ok")

    # Redundancy group ok, dependency failed - Service 6
    def test_failed_dependency_with_redundancy_group(self):
        self.assertEqual(Service.query.get(6).health, "major")

    # All dependencies failed - Service 7
    def test_all_dependency_failed(self):
        self.assertEqual(Service.query.get(7).health, "critical")

    # One dependency has no data - Service 8
    def test_no_data(self):
        self.assertEqual(Service.query.get(8).health, "ok")

    def test_member_hosts(self):
        host_ids = []
        for host in Service.query.get(3).member_hosts:
            host_ids.append(host.id)
        self.assertEqual(sorted(host_ids), [1,4])

        host_ids = []
        for host in Service.query.get(4).member_hosts:
            host_ids.append(host.id)
        self.assertEqual(sorted(host_ids), [2,4])

        host_ids = []
        for host in Service.query.get(6).member_hosts:
            host_ids.append(host.id)
        self.assertEqual(sorted(host_ids), [1,3])

        host_ids = []
        for host in Service.query.get(7).member_hosts:
            host_ids.append(host.id)
        self.assertEqual(sorted(host_ids), [3,4])

    def test_host_services(self):
        service_ids = []
        for service in Host.query.get(1).services:
            service_ids.append(service.id)
        self.assertEqual(sorted(service_ids), [1,2,3,5,6,8,9,10])

        service_ids = []
        for service in Host.query.get(3).services:
            service_ids.append(service.id)
        self.assertEqual(sorted(service_ids), [1,6,7])

        service_ids = []
        for service in Host.query.get(6).services:
            service_ids.append(service.id)
        self.assertEqual(sorted(service_ids), [8])

    def test_host_group_dependency(self):
        self.assertEqual(Service.query.get(9).health, "critical")

    def test_host_group_redundancy(self):
        self.assertEqual(Service.query.get(10).health, "degraded")

class TestAlertRestriction(unittest.TestCase):
    def setUp(self):
        session.commit()
        drop_all()
        create_all()

        session.add(Alert(id=1))
        session.add(Alert(id=2))
        session.add(Check(id=1))
        session.add(Plugin(id=1))

        session.add(AlertRestrictToEntity(alert_id=1, plugin_id=1))
        session.add(AlertRestrictToEntity(alert_id=1, check_id=1))

        session.commit()

    def test_unrestricted(self):
        a = Alert.query.get(1)
        self.assertEqual(a.is_valid(1,1), True)

    def test_valid(self):
        a = Alert.query.get(1)
        self.assertEqual(a.is_valid(1,1), True)

    def test_invalid(self):
        a = Alert.query.get(1)
        self.assertEqual(a.is_valid(2,2), False)

if __name__ == "__main__":
    unittest.main()
