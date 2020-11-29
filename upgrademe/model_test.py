import unittest
from unittest.mock import MagicMock, call
from .model import Model
from .columns import Columns
from .column_types import String, DateTime, Integer
from collections import namedtuple, OrderedDict
from datetime import datetime


class User(Model):
    def __init__(self, cursor, columns):
        super().__init__(cursor, columns)

    def columns_configuration(self):
        return OrderedDict([
            ('name', {'class': String}),
            ('birth_date', {'class': DateTime}),
            ('age', {'class': Integer})
        ])

    def pre_save(self, data):
        return {**data, **{'test': 'thingy'}}

    def post_save(self, data, id):
        self.post_save_data = data
        self.post_save_id = id
        return data

class ModelTest(unittest.TestCase):
    def setUp(self):
        # the object graph will be used by the Columns to build the ColumnType objects, which have no dependencies
        # (at least, the ones used in this test don't)
        self.object_graph = type('', (), {
            'provide': lambda class_to_build: class_to_build()
        })
        self.columns = Columns(self.object_graph)

    def test_create(self):
        user_record = namedtuple('user', ['id', 'name', 'birth_date', 'age'])
        new_user = user_record('5', 'Conor', '2020-11-28 12:30:45', '1')
        cursor = type('', (), {
            'execute': MagicMock(),
            'next': MagicMock(return_value=new_user),
            'lastrowid': 5,
        })()

        birth_date = datetime.strptime('2020-11-28 12:30:45', '%Y-%m-%d %H:%M:%S')
        user = User(cursor, self.columns)
        user.save({'name': 'Conor', 'birth_date': birth_date, 'age': '1'})
        self.assertEquals('Conor', user.name)
        self.assertEquals(birth_date, user.birth_date)
        self.assertEquals(1, user.age)
        self.assertEquals(5, user.id)
        cursor.execute.assert_has_calls([
            call('INSERT INTO `users` (`name`, `birth_date`, `age`, `test`) VALUES (?, ?, ?, ?)', ['Conor', '2020-11-28 12:30:45', '1', 'thingy']),
            call('SELECT * FROM `users` WHERE id=?', 5),
        ])
        self.assertEquals({'name': 'Conor', 'birth_date': birth_date, 'age': '1', 'test': 'thingy'}, user.post_save_data)
        self.assertEquals(5, user.post_save_id)
