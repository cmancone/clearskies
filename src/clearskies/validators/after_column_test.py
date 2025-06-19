import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from .after_column import AfterColumn


class AfterTest(unittest.TestCase):
    def setUp(self):
        self.after = AfterColumn("before_date")

    def test_check(self):
        error = self.after.check(
            SimpleNamespace(before_date=""), "after_date", {"after_date": "2024-02-27", "before_date": "2024-02-25"}
        )
        self.assertEqual("", error)
        error = self.after.check(SimpleNamespace(before_date="2024-02-25"), "after_date", {"after_date": "2024-02-27"})
        self.assertEqual("", error)
        error = self.after.check(SimpleNamespace(before_date="2024-02-25"), "after_date", {"after_date": "2024-02-25"})
        self.assertEqual("'after_date' must be after 'before_date'", error)
        error = self.after.check(
            SimpleNamespace(before_date=""), "after_date", {"after_date": "2024-02-25", "before_date": "2025-02-25"}
        )
        self.assertEqual("'after_date' must be after 'before_date'", error)
        error = self.after.check(
            SimpleNamespace(before_date=""), "after_date", {"after_date": "2024-02-27", "before_date": "2025-02-25"}
        )
        self.assertEqual("'after_date' must be after 'before_date'", error)

        after = AfterColumn("before_date", allow_equal=True)
        error = after.check(
            SimpleNamespace(before_date=""), "after_date", {"after_date": "2024-02-25", "before_date": "2024-02-25"}
        )
        self.assertEqual("", error)
