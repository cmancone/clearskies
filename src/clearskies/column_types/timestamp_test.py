import unittest
from .timestamp import Timestamp
from datetime import datetime, timezone
from unittest.mock import MagicMock


class TimestampTest(unittest.TestCase):
    def test_from_backend(self):
        datetime_column = Timestamp("di")
        datetime_column.configure("created", {}, int)
        date = datetime_column.from_backend(1715440777)
        self.assertEquals(type(date), datetime)
        self.assertEquals(2024, date.year)
        self.assertEquals(5, date.month)
        self.assertEquals(11, date.day)
        self.assertEquals(15, date.hour)
        self.assertEquals(19, date.minute)
        self.assertEquals(37, date.second)
        self.assertEquals(timezone.utc, date.tzinfo)

    def test_to_backend(self):
        date = Timestamp("di")
        date.configure("created", {}, int)
        data = date.to_backend({"created": 1715440777})
        self.assertEquals(1715440777, data["created"])

    def test_check_search_value(self):
        date = Timestamp("di")
        date.configure("created", {}, int)
        self.assertEquals("'created' must be an integer", date.check_search_value("1715440777"))
        self.assertEquals("", date.check_search_value(1715440777))
