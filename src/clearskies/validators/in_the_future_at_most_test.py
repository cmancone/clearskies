import datetime
import unittest
from unittest.mock import MagicMock

import clearskies

from .in_the_future_at_most import InTheFutureAtMost


class InTheFutureAtMostTest(unittest.TestCase):
    def setUp(self):
        di = clearskies.di.Di(utcnow=datetime.datetime(2024, 2, 25, 15, 30, tzinfo=datetime.timezone.utc))
        self.at_most = InTheFutureAtMost(datetime.timedelta(hours=5))
        self.at_most.injectable_properties(di)

    def test_check_time(self):
        error = self.at_most.check("model", "then", {"then": "2024-02-25 15:30"})
        self.assertEqual("", error)
        error = self.at_most.check("model", "then", {"then": "2024-02-25 16:30"})
        self.assertEqual("", error)
        error = self.at_most.check("model", "then", {"then": "2024-02-25 17:30"})
        self.assertEqual("", error)
        error = self.at_most.check("model", "then", {"then": "2024-02-25 20:30"})
        self.assertEqual("", error)
        error = self.at_most.check("model", "then", {"then": "2024-02-25 20:31"})
        self.assertEqual("'then' must be at most 5 hours in the future.", error)
        error = self.at_most.check("model", "then", {"then": "2024-02-24 15:30"})
        self.assertEqual("", error)
        error = self.at_most.check("model", "then", {"then": ""})
        self.assertEqual("", error)
        error = self.at_most.check("model", "then", {"then": "asdf"})
        self.assertEqual("'then' was not a valid date", error)
