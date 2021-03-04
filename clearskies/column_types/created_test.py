import unittest
from .created import Created
import datetime


class CreatedTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime.strptime('2021-01-07 22:45:13', '%Y-%m-%d %H:%M:%S')

    def test_is_writeable(self):
        created = Created(self.now)
        self.assertFalse(created.is_writeable)

    def test_pre_save(self):
        model = type('', (), {})
        model.exists = False
        created = Created(self.now)
        created.configure('created', {}, int)
        self.assertEquals({'hey': 'sup', 'created': self.now}, created.pre_save({'hey': 'sup'}, model))

        model.exists = True
        self.assertEquals({'hey': 'sup'}, created.pre_save({'hey': 'sup'}, model))
