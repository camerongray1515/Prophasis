import unittest
import sys
from prophasis_common.models import create_all, session, Host, PluginResult,\
    Plugin, CheckPlugin,Check, HostGroup, HostGroupAssignment, CheckAssignment

sys.under_unittest = True

class TestHostHealth(unittest.TestCase):
    def setUp(self):
        create_all()
        # Insert all plugins
        for letter in ["A", "B", "C", "D"]:
            p = Plugin(id=letter, name=letter)
            session.add(p)

        g = HostGroup(name="G")
        session.add(g)
        g2 = HostGroup(name="G2")
        session.add(g2)

        # Insert all hosts
        for number in range(1,8):
            h = Host(name=number)
            session.add(h)
            session.flush()
            if number in [3,4]:
                hga = HostGroupAssignment(member_host_id=h.id,
                    host_group_id=g.id)
                session.add(hga)
            if number == 7:
                hga = HostGroupAssignment(member_host_id=h.id,
                    host_group_id=g2.id)
                session.add(hga)
        hga = HostGroupAssignment(member_host_group_id=g.id,
            host_group_id=g2.id)
        session.add(hga)

        # Insert all checks and do assignments
        for number in range(1,6):
            c = Check(name=number)
            session.add(c)

        session.add(CheckAssignment(check_id=1, host_id=1))
        session.add(CheckAssignment(check_id=1, host_id=2))
        session.add(CheckAssignment(check_id=1, host_id=4))
        session.add(CheckAssignment(check_id=2, host_id=3))
        session.add(CheckAssignment(check_id=4, host_id=5))
        session.add(CheckAssignment(check_id=3, host_group_id=1))
        session.add(CheckAssignment(check_id=5, host_group_id=2))

        session.add(CheckPlugin(check_id=1, plugin_id=2))
        session.add(CheckPlugin(check_id=1, plugin_id=3))
        session.add(CheckPlugin(check_id=2, plugin_id=2))
        session.add(CheckPlugin(check_id=3, plugin_id=1))
        session.add(CheckPlugin(check_id=4, plugin_id=1))
        session.add(CheckPlugin(check_id=4, plugin_id=2))
        session.add(CheckPlugin(check_id=4, plugin_id=3))
        session.add(CheckPlugin(check_id=5, plugin_id=4))
        session.commit()

        # session.add(PluginResult(host_id=, plugin_id=, health_status))



if __name__ == "__main__":
    unittest.main()
