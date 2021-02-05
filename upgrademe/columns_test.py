import unittest
from unittest.mock import MagicMock, call
from .model import Model
from .columns import Columns
from .column_types import String, Integer
from .input_requirements import Required, MinimumLength, MaximumLength


class ColumnsTest(unittest.TestCase):
    def setUp(self):
        # the object graph will be used by the Columns to build the ColumnType objects, which have no dependencies
        # (at least, the ones used in this test don't)
        self.object_graph = type('', (), {
            'provide': lambda class_to_build: class_to_build()
        })
        self.columns = Columns(self.object_graph)

    def test_configure(self):
        columns = self.columns.configure({
            'first_name': {
                'class': String,
                'input_requirements': [Required, (MinimumLength, 2), (MaximumLength, 15)],
            },
            'last_name': {
                'class': String,
                'input_requirements': [Required],
            },
            'age': {
                'class': Integer,
            },
        }, Model)

        self.assertEquals(3, len(columns))
        self.assertTrue('first_name' in columns)
        self.assertTrue('last_name' in columns)
        self.assertTrue('age' in columns)
        self.assertEquals('first_name', columns['first_name'].name)
        self.assertEquals('last_name', columns['last_name'].name)
        self.assertEquals('age', columns['age'].name)
        self.assertEquals(3, len(columns['first_name'].config('input_requirements')))
        self.assertEquals(1, len(columns['last_name'].config('input_requirements')))
        self.assertEquals(0, len(columns['age'].config('input_requirements')))

        self.assertEquals(Required, columns['last_name'].config('input_requirements')[0].__class__)
        first_name_requirements = columns['first_name'].config('input_requirements')
        self.assertEquals(Required, first_name_requirements[0].__class__)
        self.assertEquals(MinimumLength, first_name_requirements[1].__class__)
        self.assertEquals(MaximumLength, first_name_requirements[2].__class__)
        self.assertEquals(2, first_name_requirements[1].minimum_length)
        self.assertEquals(15, first_name_requirements[2].maximum_length)
