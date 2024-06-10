import unittest
from .datetime import DateTime
from datetime import datetime, timezone
from unittest.mock import MagicMock


class DateTimeTest(unittest.TestCase):
    def test_from_backend(self):
        datetime_column = DateTime("di", timezone.utc)
        datetime_column.configure("created", {}, int)
        date = datetime_column.from_backend("2020-11-28 12:30:45")
        self.assertEqual(type(date), datetime)
        self.assertEqual(2020, date.year)
        self.assertEqual(11, date.month)
        self.assertEqual(28, date.day)
        self.assertEqual(12, date.hour)
        self.assertEqual(30, date.minute)
        self.assertEqual(45, date.second)
        self.assertEqual(timezone.utc, date.tzinfo)

    def test_to_backend(self):
        date = DateTime("di", timezone.utc)
        date.configure("created", {}, int)
        data = date.to_backend({"created": datetime.strptime("2021-01-07 22:45:13", "%Y-%m-%d %H:%M:%S")})
        self.assertEqual("2021-01-07 22:45:13", data["created"])

    def test_to_json(self):
        some_day = datetime.strptime("2021-01-07 22:45:13", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        model = type("", (), {"get": MagicMock(return_value=some_day)})()
        date = DateTime("di", timezone.utc)
        date.configure("created", {}, int)
        self.assertEqual({"created": "2021-01-07T22:45:13+00:00"}, date.to_json(model))
        model.get.assert_called_with("created", silent=True)

    def test_is_allowed_operator(self):
        date = DateTime("di", timezone.utc)
        for operator in ["=", "<", ">", "<=", ">="]:
            self.assertTrue(date.is_allowed_operator(operator))
        for operator in ["==", "<=>"]:
            self.assertFalse(date.is_allowed_operator(operator))

    def test_build_condition(self):
        date = DateTime("di", timezone.utc)
        date.configure("created", {}, int)
        self.assertEqual("created=2021-01-07 22:45:13", date.build_condition("2021-01-07 22:45:13 UTC"))
        self.assertEqual("created<2021-01-07 21:45:13", date.build_condition("2021-01-07 22:45:13 UTC+1", operator="<"))

    def test_check_search_value(self):
        date = DateTime("di", timezone.utc)
        self.assertEqual("", date.check_search_value("2021-01-07 22:45:13 UTC"))
        self.assertEqual("given value did not appear to be a valid date", date.check_search_value("asdf"))
        self.assertEqual("date is missing timezone information", date.check_search_value("2021-01-07 22:45:13"))
