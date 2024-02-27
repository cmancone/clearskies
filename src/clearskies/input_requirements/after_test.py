import unittest
from unittest.mock import MagicMock
from .after import After


class AfterTest(unittest.TestCase):
    def setUp(self):
        self.after = After()
        self.after.column_name = "after_date"

    def test_check(self):
        self.after.configure("before_date")

        error = self.after.check({"before_date": ""}, {"after_date": "2024-02-27", "before_date": "2024-02-25"})
        self.assertEquals("", error)
        error = self.after.check({"before_date": "2024-02-25"}, {"after_date": "2024-02-27"})
        self.assertEquals("", error)
        error = self.after.check({"before_date": "2024-02-25"}, {"after_date": "2024-02-25"})
        self.assertEquals("'after_date' must be after 'before_date'", error)
        error = self.after.check({"before_date": ""}, {"after_date": "2024-02-25", "before_date": "2025-02-25"})
        self.assertEquals("'after_date' must be after 'before_date'", error)
        error = self.after.check({"before_date": ""}, {"after_date": "2024-02-27", "before_date": "2025-02-25"})
        self.assertEquals("'after_date' must be after 'before_date'", error)

        self.after.configure("before_date", allow_equal=True)
        error = self.after.check({"before_date": ""}, {"after_date": "2024-02-25", "before_date": "2024-02-25"})
        self.assertEquals("", error)
