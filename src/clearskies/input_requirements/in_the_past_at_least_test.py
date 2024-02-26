import unittest
from unittest.mock import MagicMock
from .in_the_past_at_least import InThePastAtLeast
import datetime


class InThePastAtLeastTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime(2024, 2, 25, 15, 30)
        datetime_mock = MagicMock()
        datetime_mock.datetime = MagicMock()
        datetime_mock.datetime.now = MagicMock(return_value=self.now)
        self.at_least = InThePastAtLeast(datetime_mock)
        self.at_least.column_name = "then"

    def test_check_time(self):
        self.at_least.configure(datetime.timedelta(hours=5))

        error = self.at_least.check("model", {"then": "2024-02-25 10:30"})
        self.assertEquals("", error)
        error = self.at_least.check("model", {"then": "2024-02-25 9:30"})
        self.assertEquals("", error)
        error = self.at_least.check("model", {"then": "2024-02-24 13:30"})
        self.assertEquals("", error)
        error = self.at_least.check("model", {"then": "2019-02-25 10:30"})
        self.assertEquals("", error)
        error = self.at_least.check("model", {"then": "2024-02-25 10:31"})
        self.assertEquals("'then' must be at least 5 hours in the past.", error)
        error = self.at_least.check("model", {"then": ""})
        self.assertEquals("", error)
        error = self.at_least.check("model", {"then": "asdf"})
        self.assertEquals("'then' was not a valid date", error)
