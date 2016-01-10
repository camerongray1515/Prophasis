import unittest
from models import create_all, drop_all, session, Host, HostGroup,\
    HostGroupAssignment, Plugin, PluginResult

class TestGetHostMembersip(unittest.TestCase):
    def setUp(self):
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

if __name__ == "__main__":
    unittest.main()
