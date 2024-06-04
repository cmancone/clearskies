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
        created = Created("di", self.datetime, datetime.timezone.utc)
        self.assertFalse(created.is_writeable)

    def test_pre_save(self):
        model = type("", (), {})
        model.exists = False
        created = Created("di", self.datetime, datetime.timezone.utc)
        created.configure("created", {}, int)
        new_data = created.pre_save({"hey": "sup"}, model)
        self.assertEqual({"hey": "sup", "created": self.now}, new_data)
        self.assertEqual(None, new_data["created"].tzinfo)
        self.assertEqual(self.datetime.datetime.now.call_args.args, (datetime.timezone.utc,))

        model.exists = True
        self.assertEqual({"hey": "sup"}, created.pre_save({"hey": "sup"}, model))

    def test_pre_save_utc(self):
        model = type("", (), {})
        model.exists = False
        created = Created("di", self.datetime, datetime.timezone.utc )
        created.configure("created", {"utc": True}, int)
        new_data = created.pre_save({"hey": "sup"}, model)
        self.assertEqual({"hey": "sup", "created": self.now}, new_data)
        self.assertEqual(self.datetime.datetime.now.call_args.args, (datetime.timezone.utc,))

        model.exists = True
        self.assertEqual({"hey": "sup"}, created.pre_save({"hey": "sup"}, model))
