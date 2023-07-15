from unittest.mock import MagicMock
import unittest
from .created_by_authorization_data import CreatedByAuthorizationData


class CreatedByAuthorizationDataTest(unittest.TestCase):
    def test_is_writeable(self):
        created_by = CreatedByAuthorizationData("di")
        self.assertFalse(created_by.is_writeable)

    def test_pre_save(self):
        model = MagicMock()
        model.exists = False
        input_output = MagicMock()
        input_output.get_authorization_data = MagicMock(return_value={"name": "bob", "id": 12})
        di = MagicMock()
        di.build = MagicMock(return_value=input_output)
        created_by = CreatedByAuthorizationData(di)
        created_by.configure("name", {"authorization_data_key_name": "name"}, int)
        self.assertEquals({"hey": "sup", "name": "bob"}, created_by.pre_save({"hey": "sup"}, model))
        di.build.assert_called_with("input_output", cache=True)

        model.exists = True
        self.assertEquals({"hey": "sup"}, created_by.pre_save({"hey": "sup"}, model))
