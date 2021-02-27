import unittest
from .float import Float


class FloatTest(unittest.TestCase):
    def test_from_database(self):
        float_column = Float()
        self.assertEquals(5.0, float_column.from_database('5'))

    def test_is_allowed_operator(self):
        float_column = Float()
        for operator in ['=', '<', '>', '<=', '>=']:
            self.assertTrue(float_column.is_allowed_operator(operator))
        for operator in ['==', '<=>']:
            self.assertFalse(float_column.is_allowed_operator(operator))

    def test_build_condition(self):
        float_column = Float()
        float_column.configure('fraction', {}, int)
        self.assertEquals('fraction=0.2', float_column.build_condition(0.2))
        self.assertEquals(
            'fraction<10',
            float_column.build_condition(10, operator='<')
        )

    def test_check_search_value(self):
        float_column = Float()
        self.assertEquals('', float_column.check_search_value(25))
        self.assertEquals('', float_column.check_search_value(25.0))
        self.assertEquals('value should be an integer or float', float_column.check_search_value('asdf'))
