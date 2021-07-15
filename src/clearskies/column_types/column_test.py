import unittest
from .column import Column
from ..input_requirements import MinimumLength
from ..autodoc.response import String as AutoDocString


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

    def test_documentation(self):
        self.column.configure(
            'my_name',
            {'input_requirements': [self.minimum_length]},
            RealColumn
        )
        doc = self.column.documentation()

        self.assertEquals(AutoDocString, doc.__class__)
        self.assertEquals('my_name', doc.name)
        self.assertEquals('string', doc.example)

        more_doc = self.column.documentation(name='hey', example='sup', value='okay')
        self.assertEquals(AutoDocString, more_doc.__class__)
        self.assertEquals('hey', more_doc.name)
        self.assertEquals('sup', more_doc.example)
        self.assertEquals('okay', more_doc.value)
