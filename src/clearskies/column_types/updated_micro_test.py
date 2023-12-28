import unittest
from unittest.mock import MagicMock
from .updated_micro import UpdatedMicro
import datetime


class UpdatedMicroTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime.strptime("2021-01-07 22:45:13.123456", "%Y-%m-%d %H:%M:%S.%f")
        self.datetime = MagicMock()
        self.datetime.datetime = MagicMock()
        self.datetime.datetime.now = MagicMock(return_value=self.now)
        self.datetime.timezone = MagicMock()
        self.datetime.timezone.utc = datetime.timezone.utc

    def test_is_writeable(self):
        updated = UpdatedMicro("di", self.datetime)
        self.assertFalse(updated.is_writeable)

    def test_pre_save(self):
        model = type("", (), {})
        model.exists = False
        updated = UpdatedMicro("di", self.datetime)
        updated.configure("updated", {}, int)
        self.assertEquals({"hey": "sup", "updated": self.now}, updated.pre_save({"hey": "sup"}, model))

        model.exists = True
        self.assertEquals({"hey": "sup", "updated": self.now}, updated.pre_save({"hey": "sup"}, model))
