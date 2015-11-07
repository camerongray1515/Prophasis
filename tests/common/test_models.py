import unittest
from models import create_all, drop_all, session, Host, HostGroup,\
    HostGroupAssignment

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

if __name__ == "__main__":
    unittest.main()
