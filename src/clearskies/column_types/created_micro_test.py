import unittest
from .created_micro import CreatedMicro
import datetime


class CreatedTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime.strptime("2021-01-07 22:45:13.123456", "%Y-%m-%d %H:%M:%S.%f")

    def test_is_writeable(self):
        created = CreatedMicro("di", self.now)
        self.assertFalse(created.is_writeable)

    def test_pre_save(self):
        model = type("", (), {})
        model.exists = False
        created = CreatedMicro("di", self.now)
        created.configure("created", {}, int)
        self.assertEquals({"hey": "sup", "created": self.now}, created.pre_save({"hey": "sup"}, model))

        model.exists = True
        self.assertEquals({"hey": "sup"}, created.pre_save({"hey": "sup"}, model))
