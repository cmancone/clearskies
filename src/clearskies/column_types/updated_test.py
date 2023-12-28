import unittest
from unittest.mock import MagicMock
from .updated import Updated
import datetime


class UpdatedTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime.strptime("2021-01-07 22:45:13", "%Y-%m-%d %H:%M:%S")
        self.datetime = MagicMock()
        self.datetime.datetime = MagicMock()
        self.datetime.datetime.now = MagicMock(return_value=self.now)
        self.datetime.timezone = MagicMock()
        self.datetime.timezone.utc = datetime.timezone.utc

    def test_is_writeable(self):
        updated = Updated("di", self.datetime)
        self.assertFalse(updated.is_writeable)

    def test_pre_save(self):
        model = type("", (), {})
        model.exists = False
        updated = Updated("di", self.datetime)
        updated.configure("updated", {}, int)
        self.assertEquals({"hey": "sup", "updated": self.now}, updated.pre_save({"hey": "sup"}, model))

        model.exists = True
        self.assertEquals({"hey": "sup", "updated": self.now}, updated.pre_save({"hey": "sup"}, model))

    def test_pre_save_utc(self):
        model = type("", (), {})
        model.exists = True
        created = Updated("di", self.datetime)
        created.configure("created", {"utc": True}, int)
        new_data = created.pre_save({"hey": "sup"}, model)
        self.assertEquals({"hey": "sup", "created": self.now}, new_data)
        self.assertEquals(self.datetime.datetime.now.call_args.args, (datetime.timezone.utc,))
