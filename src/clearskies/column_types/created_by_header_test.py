from unittest.mock import MagicMock
import unittest
from .created_by_header import CreatedByHeader


class CreatedByHeaderTest(unittest.TestCase):
    def test_is_writeable(self):
        created_by = CreatedByHeader("id")
        self.assertFalse(created_by.is_writeable)

    def test_pre_save(self):
        model = MagicMock()
        model.exists = False
        input_output = MagicMock()
        input_output.get_request_header = MagicMock(return_value="my-header-value")
        di = MagicMock()
        di.build = MagicMock(return_value=input_output)
        created_by = CreatedByHeader(di)
        created_by.configure("name", {"header_name": "my-header"}, int)
        self.assertEquals({"hey": "sup", "name": "my-header-value"}, created_by.pre_save({"hey": "sup"}, model))
        di.build.assert_called_with("input_output", cache=True)
        input_output.get_request_header.assert_called_with("my-header")

        model.exists = True
        self.assertEquals({"hey": "sup"}, created_by.pre_save({"hey": "sup"}, model))
