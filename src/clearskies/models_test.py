import unittest
from unittest.mock import MagicMock, call
from .models import Models
from .model import Model
from .di import StandardDependencies
from . import column_types
from collections import OrderedDict


class User(Model):
    def __init__(self, cursor, column):
        super().__init__(cursor, column)

    @property
    def table_name(self):
        return 'users'

    def columns_configuration(self):
        return OrderedDict([
            column_types.string('last_name'),
            column_types.integer('age'),
            column_types.created('created'),
        ])


class Users(Models):
    _empty_model = None

    def __init__(self, cursor, columns):
        super().__init__(cursor, columns)

    def model_class(self):
        return User

    def empty_model(self):
        if self._empty_model is None:
            self._empty_model = User(self._backend, self._columns)
        return self._empty_model


class TestModels(unittest.TestCase):
    def setUp(self):
        self.backend = type('', (), {
            'count': MagicMock(return_value=10),
            'records': MagicMock(return_value=[{'id': 5, 'my': 'data'}]),
        })()
        self.di = StandardDependencies()
        self.columns = self.di.build('columns')

    def test_configure(self):
        users = Users('cursor', self.columns) \
            .where("age>5") \
            .where("age<10") \
            .group_by('last_name') \
            .sort_by('created', 'desc') \
            .join('LEFT JOIN posts ON posts.user_id=users.id') \
            .limit(5, 10) \
            .select('*')
        self.assertEquals(
            {
                'table': '',
                'column': 'age',
                'operator': '>',
                'values': ['5'],
                'parsed': 'age>%s',
            },
            users.configuration['wheres'][0]
        )
        self.assertEquals(
            {
                'table': '',
                'column': 'age',
                'operator': '<',
                'values': ['10'],
                'parsed': 'age<%s',
            },
            users.configuration['wheres'][1]
        )
        self.assertEquals({'column': 'created', 'direction': 'desc'}, users.configuration['sorts'][0])
        self.assertEquals('last_name', users.configuration['group_by_column'])
        self.assertEquals('LEFT JOIN posts ON posts.user_id=users.id', users.configuration['joins'][0]['raw'])
        self.assertEquals(5, users.configuration['limit_start'])
        self.assertEquals(10, users.configuration['limit_length'])
        self.assertEquals('*', users.configuration['selects'])

    def test_table_name(self):
        self.assertEquals('users', Users('cursor', self.columns).table_name)

    def test_build_model(self):
        user = Users('cursor', self.columns).model({'id': 2, 'age': 5})
        self.assertEquals(User, type(user))

    def test_as_sql(self):
        users = Users(self.backend, self.columns) \
            .where("age>5") \
            .where("age<10") \
            .group_by('last_name') \
            .sort_by('created', 'desc') \
            .join('LEFT JOIN posts ON posts.user_id=users.id') \
            .limit(5, 10) \
            .select('*')
        iterator = users.__iter__()
        self.backend.records.assert_has_calls([
            call({
                'wheres': [
                    {'table': '', 'column': 'age', 'operator': '>', 'values': ['5'], 'parsed': 'age>%s'},
                    {'table': '', 'column': 'age', 'operator': '<', 'values': ['10'], 'parsed': 'age<%s'}
                ],
                'sorts': [
                    {'column': 'created', 'direction': 'desc'}
                ],
                'group_by_column': 'last_name',
                'joins': [
                    {
                        'alias': '',
                        'type': 'LEFT',
                        'table': 'posts',
                        'left_table': 'users',
                        'left_column': 'id',
                        'right_table': 'posts',
                        'right_column': 'user_id',
                        'raw': 'LEFT JOIN posts ON posts.user_id=users.id',
                    }
                ],
                'limit_start': 5,
                'limit_length': 10,
                'selects': '*',
                'table_name': 'users',
                'model_columns': users.model_columns,
            }, users.empty_model())
        ])
        user = iterator.__next__()
        self.assertEquals(User, user.__class__)
        self.assertEquals({'id': 5, 'my': 'data'}, user._data)

    def test_as_sql_empty(self):
        users = Users(self.backend, self.columns)
        users.__iter__()
        self.backend.records.assert_has_calls([
            call({
                'wheres': [],
                'sorts': [],
                'group_by_column': None,
                'joins': [],
                'limit_start': 0,
                'limit_length': None,
                'selects': None,
                'table_name': 'users',
                'model_columns': None,
            }, users.empty_model())
        ])

    def test_length(self):
        users = Users(self.backend, self.columns) \
            .where("age>5") \
            .where("age<10") \
            .sort_by('created', 'desc') \
            .join('JOIN posts ON posts.user_id=users.id') \
            .join('LEFT JOIN more_posts ON more_posts.user_id=users.id') \
            .limit(5, 10) \
            .select('*')
        count = len(users)
        self.assertEquals(10, count)
        self.backend.count.assert_has_calls([
            call({
                'wheres': [
                    {'table': '', 'column': 'age', 'operator': '>', 'values': ['5'], 'parsed': 'age>%s'},
                    {'table': '', 'column': 'age', 'operator': '<', 'values': ['10'], 'parsed': 'age<%s'}
                ],
                'sorts': [
                    {'column': 'created', 'direction': 'desc'}
                ],
                'group_by_column': None,
                'joins': [
                    {
                        'alias': '',
                        'type': 'INNER',
                        'table': 'posts',
                        'left_table': 'users',
                        'left_column': 'id',
                        'right_table': 'posts',
                        'right_column': 'user_id',
                        'raw': 'JOIN posts ON posts.user_id=users.id',
                    },
                    {
                        'alias': '',
                        'type': 'LEFT',
                        'table': 'more_posts',
                        'left_table': 'users',
                        'left_column': 'id',
                        'right_table': 'more_posts',
                        'right_column': 'user_id',
                        'raw': 'LEFT JOIN more_posts ON more_posts.user_id=users.id',
                    },
                ],
                'limit_start': 5,
                'limit_length': 10,
                'selects': '*',
                'table_name': 'users',
                'model_columns': users.model_columns,
            }, users.empty_model())
        ])
