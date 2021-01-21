import unittest
from .datetime import DateTime
from datetime import datetime, timezone
from unittest.mock import MagicMock


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
        self.assertEquals(timezone.utc, date.tzinfo)

    def test_to_database(self):
        date = DateTime()
        date.configure('created', {}, 'model')
        data = date.to_database({'created': datetime.strptime('2021-01-07 22:45:13', '%Y-%m-%d %H:%M:%S')})
        self.assertEquals('2021-01-07 22:45:13', data['created'])

    def test_to_json(self):
        some_day = datetime.strptime('2021-01-07 22:45:13', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        model = type('', (), {'__getattr__': MagicMock(return_value=some_day)})()
        date = DateTime()
        date.configure('created', {}, 'model')
        self.assertEquals('2021-01-07T22:45:13+00:00', date.to_json(model))
        model.__getattr__.assert_called_with('created')
