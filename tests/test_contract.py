import unittest
from tools.check_contract import check


class ContractSmoke(unittest.TestCase):
    def test_shared_fixture_wires(self):
        self.assertEqual(check(), 3)
