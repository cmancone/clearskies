import unittest
from collections import OrderedDict
from unittest.mock import MagicMock, call
from ..mocks import InputOutput
from ..backends import MemoryBackend
from ..model import Model
from ..models import Models
from ..column_types import string, integer
from .list import List
from .simple_routing import SimpleRouting
from ..authentication import public, secret_bearer
from ..di import StandardDependencies
class User(Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            string('name'),
            integer('age'),
        ])
class Status(Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            string('name'),
            integer('order'),
        ])
class SimpleRoutingTest(unittest.TestCase):
    def setUp(self):
        self.input_output = InputOutput()

        self.memory_backend = MemoryBackend()
        self.memory_backend.create_table(User)
        self.memory_backend.create_record_with_class(User, {
            'id': '1-2-3-4',
            'name': 'Conor',
            'age': 120,
        })
        self.memory_backend.create_record_with_class(User, {
            'id': '1-2-3-5',
            'name': 'Enoch',
            'age': 30,
        })

        self.memory_backend.create_table(Status)
        self.memory_backend.create_record_with_class(Status, {
            'id': '1-2-3-6',
            'name': 'Active',
            'order': 1,
        })
        self.memory_backend.create_record_with_class(Status, {
            'id': '1-2-3-7',
            'name': 'Inactive',
            'order': 2,
        })

        self.di = StandardDependencies()
        self.di.bind('input_output', self.input_output)
        self.di.bind('cursor_backend', self.memory_backend)

        self.handler = SimpleRouting(self.di)
        self.handler.configure({
            'authentication':
            public(),
            'schema_route':
            'schema',
            'schema_authentication':
            secret_bearer(secret='asdfer'),
            'routes': [
                {
                    'methods': 'SECRET',
                    'handler_class': List,
                    'handler_config': {
                        'model_class': Status,
                        'readable_columns': ['name', 'order'],
                        'searchable_columns': ['name', 'order'],
                        'sortable_columns': ['name', 'order'],
                        'default_sort_column': 'name',
                    },
                },
                {
                    'path': '/users/',
                    'handler_class': List,
                    'handler_config': {
                        'model_class': User,
                        'readable_columns': ['name', 'age'],
                        'searchable_columns': ['name'],
                        'sortable_columns': ['name', 'age'],
                        'default_sort_column': 'name',
                    },
                },
                {
                    'path': '/statuses/',
                    'handler_class': List,
                    'handler_config': {
                        'model_class': Status,
                        'readable_columns': ['name'],
                        'searchable_columns': ['name'],
                        'sortable_columns': ['name'],
                        'default_sort_column': 'name',
                    },
                },
            ],
        })

    def test_routing_users(self):
        self.input_output.set_request_url('/users/')
        self.input_output.set_request_method('ANY')
        result = self.handler(self.input_output)

        self.assertEquals(200, result[1])
        self.assertEquals({
            'status':
            'success',
            'data': [
                OrderedDict([
                    ('id', '1-2-3-4'),
                    ('name', 'Conor'),
                    ('age', 120),
                ]),
                OrderedDict([
                    ('id', '1-2-3-5'),
                    ('name', 'Enoch'),
                    ('age', 30),
                ]),
            ],
            'pagination': {
                'number_results': 2,
                'next_page': {},
                'limit': 100,
            },
            'error':
            '',
            'input_errors': {},
        }, result[0])

    def test_routing_statuses(self):
        self.input_output.set_request_url('/statuses/')
        self.input_output.set_request_method('ANY')
        result = self.handler(self.input_output)

        self.assertEquals(200, result[1])
        self.assertEquals({
            'status':
            'success',
            'data': [
                OrderedDict([
                    ('id', '1-2-3-6'),
                    ('name', 'Active'),
                ]),
                OrderedDict([
                    ('id', '1-2-3-7'),
                    ('name', 'Inactive'),
                ]),
            ],
            'pagination': {
                'number_results': 2,
                'next_page': {},
                'limit': 100,
            },
            'error':
            '',
            'input_errors': {},
        }, result[0])

    def test_routing_secret(self):
        self.input_output.set_request_url('')
        self.input_output.set_request_method('secret')
        result = self.handler(self.input_output)

        self.assertEquals(200, result[1])
        self.assertEquals({
            'status':
            'success',
            'data': [
                OrderedDict([
                    ('id', '1-2-3-6'),
                    ('name', 'Active'),
                    ('order', 1),
                ]),
                OrderedDict([
                    ('id', '1-2-3-7'),
                    ('name', 'Inactive'),
                    ('order', 2),
                ]),
            ],
            'pagination': {
                'number_results': 2,
                'next_page': {},
                'limit': 100,
            },
            'error':
            '',
            'input_errors': {},
        }, result[0])

    def test_schema_authentication(self):
        self.input_output.set_request_url('schema')
        result = self.handler(self.input_output)

        self.assertEquals(401, result[1])
        self.assertEquals({
            'status': 'client_error',
            'data': [],
            'pagination': {},
            'error': 'Not Authenticated',
            'input_errors': {},
        }, result[0])

    def test_documentation(self):
        docs = self.handler.documentation()
        self.assertEquals(['', 'users', 'statuses'], [doc.relative_path for doc in docs])
        self.assertEquals(['SECRET', 'GET', 'GET'], [doc.request_methods[0] for doc in docs])
