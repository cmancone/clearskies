import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from .before_column import BeforeColumn


class BeforeTest(unittest.TestCase):
    def setUp(self):
        self.before = BeforeColumn("after_date")

    def test_check(self):
        error = self.before.check(
            SimpleNamespace(after_date=""), "before_date", {"after_date": "2024-02-27", "before_date": "2024-02-25"}
        )
        self.assertEqual("", error)
        error = self.before.check(
            SimpleNamespace(after_date="2024-02-25"), "before_date", {"before_date": "2024-02-24"}
        )
        self.assertEqual("", error)
        error = self.before.check(
            SimpleNamespace(after_date="2024-02-25"), "before_date", {"before_date": "2024-02-25"}
        )
        self.assertEqual("'before_date' must be before 'after_date'", error)
        error = self.before.check(
            SimpleNamespace(after_date=""), "before_date", {"before_date": "2024-02-27", "after_date": "2023-02-25"}
        )
        self.assertEqual("'before_date' must be before 'after_date'", error)

        before = BeforeColumn("after_date", allow_equal=True)
        error = before.check(
            SimpleNamespace(after_date=""), "before_date", {"before_date": "2024-02-25", "after_date": "2024-02-25"}
        )
        self.assertEqual("", error)
