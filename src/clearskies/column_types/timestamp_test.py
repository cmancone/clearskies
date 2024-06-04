import unittest
from .timestamp import Timestamp
from datetime import datetime, timezone
from unittest.mock import MagicMock


class TimestampTest(unittest.TestCase):
    def test_from_backend(self):
        datetime_column = Timestamp("di", timezone.utc)
        datetime_column.configure("created", {}, int)
        date = datetime_column.from_backend(1715440777)
        self.assertEqual(type(date), datetime)
        self.assertEqual(2024, date.year)
        self.assertEqual(5, date.month)
        self.assertEqual(11, date.day)
        self.assertEqual(15, date.hour)
        self.assertEqual(19, date.minute)
        self.assertEqual(37, date.second)
        self.assertEqual(timezone.utc, date.tzinfo)

    def test_to_backend(self):
        date = Timestamp("di", timezone.utc)
        date.configure("created", {}, int)
        data = date.to_backend({"created": 1715440777})
        self.assertEqual(1715440777, data["created"])

    def test_check_search_value(self):
        date = Timestamp("di",timezone.utc)
        date.configure("created", {}, int)
        self.assertEqual("'created' must be an integer", date.check_search_value("1715440777"))
        self.assertEqual("", date.check_search_value(1715440777))
