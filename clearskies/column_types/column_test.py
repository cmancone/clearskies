import unittest
from .column import Column
from ..input_requirements import MinimumLength


class RealColumn(Column):
    def check_input(self, model, data):
        if 'name' in data and data['name'] == 'me':
            return 'You are not allowed'

class ColumnTest(unittest.TestCase):
    def setUp(self):
        self.column = RealColumn()
        self.minimum_length = MinimumLength()
        self.minimum_length.column_name = 'name'
        self.minimum_length.configure(10)

    def test_input_errors_requirements(self):
        self.column.configure(
            'name',
            {'input_requirements': [self.minimum_length]},
            RealColumn
        )
        errors = self.column.input_errors('model', {'name': 'a'})
        self.assertEquals({'name': "'name' must be at least 10 characters long."}, errors)
        errors = self.column.input_errors('model', {'name': 'me'})
        self.assertEquals({'name': "You are not allowed"}, errors)
        errors = self.column.input_errors('model', {'name': '1234567890'})
        self.assertEquals({}, errors)
        errors = self.column.input_errors('model', {'age': '1234567890'})
        self.assertEquals({}, errors)
