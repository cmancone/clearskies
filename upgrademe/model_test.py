import unittest
from unittest.mock import MagicMock, call
from .model import Model
from .columns import Columns
from .column_types import Column, String, DateTime, Integer
from collections import namedtuple, OrderedDict
from datetime import datetime, timezone


class ProvideTest(Column):
    def can_provide(self, column_name):
        return column_name == 'blahbblah'

    def provide(self, data, column_name):
        return data['name'] + ' blahblah'

class User(Model):
    def __init__(self, backend, columns):
        super().__init__(backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            ('name', {'class': String}),
            ('birth_date', {'class': DateTime}),
            ('age', {'class': Integer}),
            ('whatever', {'class': ProvideTest})
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
        new_user = {'id': '5', 'name': 'Conor', 'birth_date': '2020-11-28 12:30:45', 'age': '1'}
        backend = type('', (), {
            'create': MagicMock(return_value=new_user),
        })()

        birth_date = datetime.strptime('2020-11-28 12:30:45', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        user = User(backend, self.columns)
        user.save({'name': 'Conor', 'birth_date': birth_date, 'age': '1'})
        self.assertEquals('Conor', user.name)
        self.assertEquals(birth_date, user.birth_date)
        self.assertEquals(1, user.age)
        self.assertEquals(5, user.id)
        backend.create.assert_called_with({
            'name': 'Conor',
            'birth_date': '2020-11-28 12:30:45',
            'age': '1',
            'test': 'thingy',
        },  user)
        self.assertEquals({'name': 'Conor', 'birth_date': birth_date, 'age': '1', 'test': 'thingy'}, user.post_save_data)
        self.assertEquals(5, user.post_save_id)

    def test_update(self):
        old_user = {'id': '5', 'name': 'Ronoc', 'birth_date': '2019-11-28 23:30:30', 'age': '2'}
        new_user = {'id': '5', 'name': 'Conor', 'birth_date': '2020-11-28 12:30:45', 'age': '1'}
        backend = type('', (), {
            'update': MagicMock(return_value=new_user),
        })()

        birth_date = datetime.strptime('2020-11-28 12:30:45', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        user = User(backend, self.columns)
        user.data = old_user
        user.save({'name': 'Conor', 'birth_date': birth_date, 'age': '1'})
        self.assertEquals('Conor', user.name)
        self.assertEquals(birth_date, user.birth_date)
        self.assertEquals(1, user.age)
        self.assertEquals(5, user.id)
        backend.update.assert_called_with(5, {
            'name': 'Conor',
            'birth_date': '2020-11-28 12:30:45',
            'age': '1',
            'test': 'thingy',
        },  user)
        self.assertEquals({'name': 'Conor', 'birth_date': birth_date, 'age': '1', 'test': 'thingy'}, user.post_save_data)
        self.assertEquals(5, user.post_save_id)

    def test_delete(self):
        user_data = {'id': '5', 'name': 'Ronoc', 'birth_date': '', 'age': '2'}
        backend = type('', (), {
            'delete': MagicMock(return_value=True),
        })()

        user = User(backend, self.columns)
        user.data = user_data
        user.delete()
        # for now, the model isn't cleared (in case the information is needed for reference)
        self.assertEquals(True, user.exists)
        self.assertEquals('Ronoc', user.name)
        backend.delete.assert_called_with(5, user)

    def test_column_provide(self):
        user = User('cursor', self.columns)
        user.data = {
            'id': 5,
            'name': 'hey'
        }
        self.assertEquals('hey blahblah', user.blahbblah)

    def test_get_simple(self):
        user = User('cursor', self.columns)
        user.data = {'id': 5, 'name': 'hey'}
        self.assertEquals(5, user.id)
        self.assertEquals('hey', user.name)
        self.assertEquals(True, user.exists)
        with self.assertRaises(KeyError) as context:
            user.blah
        self.assertEquals("\"Unknown column 'blah' requested from model 'User'\"", str(context.exception))

    def test_get_simple_empty(self):
        user = User('cursor', self.columns)
        self.assertEquals(False, user.exists)
        self.assertEquals(None, user.id)
