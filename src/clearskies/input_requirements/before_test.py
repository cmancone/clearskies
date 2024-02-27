import unittest
from unittest.mock import MagicMock
from .before import Before


class AfterTest(unittest.TestCase):
    def setUp(self):
        self.before = Before()
        self.before.column_name = "before_date"

    def test_check(self):
        self.before.configure("after_date")

        error = self.before.check({"after_date": ""}, {"after_date": "2024-02-27", "before_date": "2024-02-25"})
        self.assertEquals("", error)
        error = self.before.check({"after_date": "2024-02-25"}, {"before_date": "2024-02-24"})
        self.assertEquals("", error)
        error = self.before.check({"after_date": "2024-02-25"}, {"before_date": "2024-02-25"})
        self.assertEquals("'before_date' must be before 'after_date'", error)
        error = self.before.check({"after_date": ""}, {"before_date": "2024-02-27", "after_date": "2023-02-25"})
        self.assertEquals("'before_date' must be before 'after_date'", error)

        self.before.configure("after_date", allow_equal=True)
        error = self.before.check({"after_date": ""}, {"before_date": "2024-02-25", "after_date": "2024-02-25"})
        self.assertEquals("", error)
