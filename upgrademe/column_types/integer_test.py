import unittest
from .integer import Integer


class IntegerTest(unittest.TestCase):
    def test_from_database(self):
        integer = Integer()
        self.assertEquals(5, integer.from_database('5'))
