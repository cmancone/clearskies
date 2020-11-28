import unittest
from .datetime import DateTime
from datetime import datetime


class DateTimeTest(unittest.TestCase):
    def test_from_database(self):
        date = DateTime().from_database('2020-11-28 12:30:45')
        self.assertEquals(type(date), datetime)
        self.assertEquals(2020, date.year)
        self.assertEquals(11, date.month)
        self.assertEquals(28, date.day)
        self.assertEquals(12, date.hour)
        self.assertEquals(30, date.minute)
        self.assertEquals(45, date.second)

    def test_to_database(self):
        date = DateTime()
        date.configure('created', {}, 'model')
        data = date.to_database({'created': datetime.strptime('2021-01-07 22:45:13', '%Y-%m-%d %H:%M:%S')})
        self.assertEquals('2021-01-07 22:45:13', data['created'])
