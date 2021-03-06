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
        self.assertEquals({'age': 'Invalid input: age must be an integer'}, error)

    def test_check_input_good(self):
        integer = Integer()
        integer.configure('age', {}, IntegerTest)
        self.assertEquals({}, integer.input_errors('model', {'age': 15}))
        self.assertEquals({}, integer.input_errors('model', {'age': None}))
        self.assertEquals({}, integer.input_errors('model', {}))
