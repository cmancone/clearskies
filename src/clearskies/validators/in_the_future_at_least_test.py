import datetime
import unittest
from unittest.mock import MagicMock

import clearskies

from .in_the_future_at_least import InTheFutureAtLeast


class InTheFutureAtLeastTest(unittest.TestCase):
    def setUp(self):
        di = clearskies.di.Di(utcnow=datetime.datetime(2024, 2, 25, 15, 30, tzinfo=datetime.timezone.utc))
        self.at_least = InTheFutureAtLeast(datetime.timedelta(hours=5))
        self.at_least.injectable_properties(di)

    def test_check_time(self):
        error = self.at_least.check("model", "then", {"then": "2024-02-25 21:30"})
        self.assertEqual("", error)
        error = self.at_least.check("model", "then", {"then": "2024-02-25 22:30"})
        self.assertEqual("", error)
        error = self.at_least.check("model", "then", {"then": "2024-02-26 13:30"})
        self.assertEqual("", error)
        error = self.at_least.check("model", "then", {"then": "2019-02-27 20:30"})
        self.assertEqual("'then' must be at least 5 hours in the future.", error)
        error = self.at_least.check("model", "then", {"then": "2024-02-25 20:29"})
        self.assertEqual("'then' must be at least 5 hours in the future.", error)
        error = self.at_least.check("model", "then", {"then": ""})
        self.assertEqual("", error)
        error = self.at_least.check("model", "then", {"then": "asdf"})
        self.assertEqual("'then' was not a valid date", error)
