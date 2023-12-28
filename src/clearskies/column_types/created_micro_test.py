import unittest
from unittest.mock import MagicMock
from .created_micro import CreatedMicro
import datetime


class CreatedTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime.strptime("2021-01-07 22:45:13.123456", "%Y-%m-%d %H:%M:%S.%f")
        self.datetime = MagicMock()
        self.datetime.datetime = MagicMock()
        self.datetime.datetime.now = MagicMock(return_value=self.now)
        self.datetime.timezone = MagicMock()
        self.datetime.timezone.utc = datetime.timezone.utc

    def test_is_writeable(self):
        created = CreatedMicro("di", self.datetime)
        self.assertFalse(created.is_writeable)

    def test_pre_save(self):
        model = type("", (), {})
        model.exists = False
        created = CreatedMicro("di", self.datetime)
        created.configure("created", {}, int)
        self.assertEquals({"hey": "sup", "created": self.now}, created.pre_save({"hey": "sup"}, model))

        model.exists = True
        self.assertEquals({"hey": "sup"}, created.pre_save({"hey": "sup"}, model))
