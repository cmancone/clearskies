import unittest
from unittest.mock import MagicMock
from .in_the_past_at_most import InThePastAtMost
import datetime


class InThePastAtMostTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime(2024, 2, 25, 15, 30)
        datetime_mock = MagicMock()
        datetime_mock.datetime = MagicMock()
        datetime_mock.datetime.now = MagicMock(return_value=self.now)
        self.at_most = InThePastAtMost(datetime_mock)
        self.at_most.column_name = "then"

    def test_check_time(self):
        self.at_most.configure(datetime.timedelta(hours=5))

        error = self.at_most.check("model", {"then": "2024-02-25 15:30"})
        self.assertEquals("", error)
        error = self.at_most.check("model", {"then": "2024-02-25 14:30"})
        self.assertEquals("", error)
        error = self.at_most.check("model", {"then": "2024-02-25 13:30"})
        self.assertEquals("", error)
        error = self.at_most.check("model", {"then": "2024-02-25 10:30"})
        self.assertEquals("", error)
        error = self.at_most.check("model", {"then": "2024-02-25 10:29"})
        self.assertEquals("'then' must be at most 5 hours in the past.", error)
        error = self.at_most.check("model", {"then": "2024-02-26 15:30"})
        self.assertEquals("", error)
        error = self.at_most.check("model", {"then": ""})
        self.assertEquals("", error)
        error = self.at_most.check("model", {"then": "asdf"})
        self.assertEquals("'then' was not a valid date", error)
