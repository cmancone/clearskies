import unittest
from .updated import Updated
import datetime


class UpdatedTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime.strptime('2021-01-07 22:45:13', '%Y-%m-%d %H:%M:%S')

    def test_is_writeable(self):
        updated = Updated(self.now)
        self.assertFalse(updated.is_writeable)

    def test_pre_save(self):
        model = type('', (), {})
        model.exists = False
        updated = Updated(self.now)
        updated.configure('updated', {}, int)
        self.assertEquals({'hey': 'sup', 'updated': self.now}, updated.pre_save({'hey': 'sup'}, model))

        model.exists = True
        self.assertEquals({'hey': 'sup', 'updated': self.now}, updated.pre_save({'hey': 'sup'}, model))
