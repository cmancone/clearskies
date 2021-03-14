import unittest
from .integer import Integer


class IntegerTest(unittest.TestCase):
    def test_from_database(self):
        integer = Integer()
        self.assertEquals(5, integer.from_database('5'))

    def test_check_input_bad(self):
        integer = Integer()
        integer.configure('age', {}, IntegerTest)
        error = integer.input_errors('model', {'age': 'asdf'})
        self.assertEquals({'age': 'age must be an integer'}, error)

    def test_check_input_good(self):
        integer = Integer()
        integer.configure('age', {}, IntegerTest)
        self.assertEquals({}, integer.input_errors('model', {'age': 15}))
        self.assertEquals({}, integer.input_errors('model', {'age': None}))
        self.assertEquals({}, integer.input_errors('model', {}))

    def test_is_allowed_operator(self):
        integer = Integer()
        for operator in ['=', '<', '>', '<=', '>=']:
            self.assertTrue(integer.is_allowed_operator(operator))
        for operator in ['==', '<=>']:
            self.assertFalse(integer.is_allowed_operator(operator))

    def test_build_condition(self):
        integer = Integer()
        integer.configure('fraction', {}, int)
        self.assertEquals('fraction=0.2', integer.build_condition(0.2))
        self.assertEquals(
            'fraction<10',
            integer.build_condition(10, operator='<')
        )

    def test_check_search_value(self):
        integer = Integer()
        integer.configure('age', {}, IntegerTest)
        self.assertEquals('', integer.check_search_value(25))
        self.assertEquals('age must be an integer', integer.check_search_value(25.0))
        self.assertEquals('age must be an integer', integer.check_search_value('asdf'))
