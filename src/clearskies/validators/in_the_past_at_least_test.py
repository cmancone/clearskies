import datetime
import unittest
from unittest.mock import MagicMock

import clearskies

from .in_the_past_at_least import InThePastAtLeast


class InThePastAtLeastTest(unittest.TestCase):
    def setUp(self):
        di = clearskies.di.Di(utcnow=datetime.datetime(2024, 2, 25, 15, 30, tzinfo=datetime.timezone.utc))
        self.at_least = InThePastAtLeast(datetime.timedelta(hours=5))
        self.at_least.injectable_properties(di)

    def test_check_time(self):
        error = self.at_least.check("model", "then", {"then": "2024-02-25 10:30+00:00"})
        self.assertEqual("", error)
        error = self.at_least.check("model", "then", {"then": "2024-02-25 9:30+00:00"})
        self.assertEqual("", error)
        error = self.at_least.check("model", "then", {"then": "2024-02-24 13:30+00:00"})
        self.assertEqual("", error)
        error = self.at_least.check("model", "then", {"then": "2019-02-25 10:30+00:00"})
        self.assertEqual("", error)
        error = self.at_least.check("model", "then", {"then": "2024-02-25 10:31+00:00"})
        self.assertEqual("'then' must be at least 5 hours in the past.", error)
        error = self.at_least.check("model", "then", {"then": ""})
        self.assertEqual("", error)
        error = self.at_least.check("model", "then", {"then": "asdf"})
        self.assertEqual("'then' was not a valid date", error)
