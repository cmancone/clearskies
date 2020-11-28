import unittest
from .float import Float


class FloatTest(unittest.TestCase):
    def test_from_database(self):
        flt = Float()
        self.assertEquals(5.0, flt.from_database('5'))
