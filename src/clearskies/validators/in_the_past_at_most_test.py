import datetime
import unittest
from unittest.mock import MagicMock

import clearskies

from .in_the_past_at_most import InThePastAtMost


class InThePastAtMostTest(unittest.TestCase):
    def setUp(self):
        di = clearskies.di.Di(utcnow=datetime.datetime(2024, 2, 25, 15, 30, tzinfo=datetime.timezone.utc))
        self.at_most = InThePastAtMost(datetime.timedelta(hours=5))
        self.at_most.injectable_properties(di)

    def test_check_time(self):
        error = self.at_most.check("model", "then", {"then": "2024-02-25 15:30"})
        self.assertEqual("", error)
        error = self.at_most.check("model", "then", {"then": "2024-02-25 14:30"})
        self.assertEqual("", error)
        error = self.at_most.check("model", "then", {"then": "2024-02-25 13:30"})
        self.assertEqual("", error)
        error = self.at_most.check("model", "then", {"then": "2024-02-25 10:30"})
        self.assertEqual("", error)
        error = self.at_most.check("model", "then", {"then": "2024-02-25 10:29"})
        self.assertEqual("'then' must be at most 5 hours in the past.", error)
        error = self.at_most.check("model", "then", {"then": "2024-02-26 15:30"})
        self.assertEqual("", error)
        error = self.at_most.check("model", "then", {"then": ""})
        self.assertEqual("", error)
        error = self.at_most.check("model", "then", {"then": "asdf"})
        self.assertEqual("'then' was not a valid date", error)
