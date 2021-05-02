import unittest
from unittest.mock import MagicMock, call
from .belongs_to import BelongsTo
from ..mocks.models import Models
from .string import String


class BelongsToTest(unittest.TestCase):
    def test_simple(self):
        self.assertTrue(True)
