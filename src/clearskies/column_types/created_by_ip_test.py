from unittest.mock import MagicMock
import unittest
from .created_by_ip import CreatedByIp


class CreatedByIpTest(unittest.TestCase):
    def test_is_writeable(self):
        created_by = CreatedByIp("di")
        self.assertFalse(created_by.is_writeable)

    def test_pre_save(self):
        model = MagicMock()
        model.exists = False
        input_output = MagicMock()
        input_output.get_client_ip = MagicMock(return_value="192.168.0.1")
        di = MagicMock()
        di.build = MagicMock(return_value=input_output)
        created_by = CreatedByIp(di)
        created_by.configure("name", {}, int)
        self.assertEqual({"hey": "sup", "name": "192.168.0.1"}, created_by.pre_save({"hey": "sup"}, model))
        di.build.assert_called_with("input_output", cache=True)
        input_output.get_client_ip.assert_called()

        model.exists = True
        self.assertEqual({"hey": "sup"}, created_by.pre_save({"hey": "sup"}, model))
