import unittest
from .select import Select


class SelectTest(unittest.TestCase):
    def test_check_input_bad(self):
        select = Select("di")
        select.configure("status", {"values": ["hey", "bob"]}, SelectTest)
        error = select.input_errors("model", {"status": "cool"})
        self.assertEqual({"status": "Invalid value for status"}, error)

    def test_check_input_good(self):
        select = Select("di")
        select.configure("status", {"values": ["hey", "bob"]}, SelectTest)
        self.assertEqual({}, select.input_errors("model", {"status": "hey"}))
        self.assertEqual({}, select.input_errors("model", {"status": ""}))
        self.assertEqual({}, select.input_errors("model", {"status": None}))
        self.assertEqual({}, select.input_errors("model", {}))
