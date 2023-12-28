import unittest
from unittest.mock import MagicMock
from .created import Created
import datetime


class CreatedTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime.strptime("2021-01-07 22:45:13", "%Y-%m-%d %H:%M:%S")
        self.datetime = MagicMock()
        self.datetime.datetime = MagicMock()
        self.datetime.datetime.now = MagicMock(return_value=self.now)
        self.datetime.timezone = MagicMock()
        self.datetime.timezone.utc = datetime.timezone.utc

    def test_is_writeable(self):
        created = Created("di", self.datetime)
        self.assertFalse(created.is_writeable)

    def test_pre_save(self):
        model = type("", (), {})
        model.exists = False
        created = Created("di", self.datetime)
        created.configure("created", {}, int)
        new_data = created.pre_save({"hey": "sup"}, model)
        self.assertEquals({"hey": "sup", "created": self.now}, new_data)
        self.assertEquals(None, new_data["created"].tzinfo)
        self.assertEquals(self.datetime.datetime.now.call_args.args, ())

        model.exists = True
        self.assertEquals({"hey": "sup"}, created.pre_save({"hey": "sup"}, model))

    def test_pre_save_utc(self):
        model = type("", (), {})
        model.exists = False
        created = Created("di", self.datetime)
        created.configure("created", {"utc": True}, int)
        new_data = created.pre_save({"hey": "sup"}, model)
        self.assertEquals({"hey": "sup", "created": self.now}, new_data)
        self.assertEquals(self.datetime.datetime.now.call_args.args, (datetime.timezone.utc,))

        model.exists = True
        self.assertEquals({"hey": "sup"}, created.pre_save({"hey": "sup"}, model))
