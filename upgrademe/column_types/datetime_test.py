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
        date.configure('created', {}, int)
        data = date.to_database({'created': datetime.strptime('2021-01-07 22:45:13', '%Y-%m-%d %H:%M:%S')})
        self.assertEquals('2021-01-07 22:45:13', data['created'])

    def test_to_json(self):
        some_day = datetime.strptime('2021-01-07 22:45:13', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        model = type('', (), {'__getattr__': MagicMock(return_value=some_day)})()
        date = DateTime()
        date.configure('created', {}, int)
        self.assertEquals('2021-01-07T22:45:13+00:00', date.to_json(model))
        model.__getattr__.assert_called_with('created')

    def test_is_allowed_operator(self):
        date = DateTime()
        for operator in ['=', '<', '>', '<=', '>=']:
            self.assertTrue(date.is_allowed_operator(operator))
        for operator in ['==', '<=>']:
            self.assertFalse(date.is_allowed_operator(operator))

    def test_build_condition(self):
        date = DateTime()
        date.configure('created', {}, int)
        self.assertEquals('created=2021-01-07 22:45:13', date.build_condition('2021-01-07 22:45:13 UTC'))
        self.assertEquals(
            'created<2021-01-07 21:45:13',
            date.build_condition('2021-01-07 22:45:13 UTC+1', operator='<')
        )

    def test_check_search_value(self):
        date = DateTime()
        self.assertEquals('', date.check_search_value('2021-01-07 22:45:13 UTC'))
        self.assertEquals('given value did not appear to be a valid date', date.check_search_value('asdf'))
        self.assertEquals('date is missing timezone information', date.check_search_value('2021-01-07 22:45:13'))
