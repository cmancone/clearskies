import unittest
from unittest.mock import MagicMock
from .in_the_future_at_least import InTheFutureAtLeast
import datetime


class InTheFutureAtLeastTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime(2024, 2, 25, 15, 30)
        datetime_mock = MagicMock()
        datetime_mock.datetime = MagicMock()
        datetime_mock.datetime.now = MagicMock(return_value=self.now)
        self.at_least = InTheFutureAtLeast(datetime_mock)
        self.at_least.column_name = "then"

    def test_check_time(self):
        self.at_least.configure(datetime.timedelta(hours=5))

        error = self.at_least.check("model", {"then": "2024-02-25 21:30"})
        self.assertEqual("", error)
        error = self.at_least.check("model", {"then": "2024-02-25 22:30"})
        self.assertEqual("", error)
        error = self.at_least.check("model", {"then": "2024-02-26 13:30"})
        self.assertEqual("", error)
        error = self.at_least.check("model", {"then": "2019-02-27 20:30"})
        self.assertEqual("'then' must be at least 5 hours in the future.", error)
        error = self.at_least.check("model", {"then": "2024-02-25 20:29"})
        self.assertEqual("'then' must be at least 5 hours in the future.", error)
        error = self.at_least.check("model", {"then": ""})
        self.assertEqual("", error)
        error = self.at_least.check("model", {"then": "asdf"})
        self.assertEqual("'then' was not a valid date", error)
