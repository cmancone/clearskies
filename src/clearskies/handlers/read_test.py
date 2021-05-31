import unittest
from .read import Read
from ..mocks import Models, InputOutput
from ..column_types import String, Integer
from ..authentication import Public, SecretBearer
from ..di import StandardDependencies


class ReadTest(unittest.TestCase):
    def setUp(self):
        self.di = StandardDependencies()
        Models.reset()
        self.models = Models({
            'name': {'class': String},
            'email': {'class': String},
            'age': {'class': Integer},
        })
        self.models.add_search_response([
            {'id': 5, 'name': 'conor', 'email': 'cmancone1@example.com', 'age': '15'},
            {'id': 8, 'name': 'ronoc', 'email': 'cmancone2@example.com', 'age': 25},
        ])
        self.models.add_search_response([
            {'id': 5, 'name': 'conor', 'email': 'cmancone1@example.com', 'age': 15},
            {'id': 8, 'name': 'ronoc', 'email': 'cmancone2@example.com', 'age': 25},
        ])

    def test_simple_read(self):
        read = Read(self.di)
        read.configure({
            'models': self.models,
            'readable_columns': ['name', 'email', 'age'],
            'searchable_columns': ['name'],
            'default_sort_column': 'email',
            'authentication': Public(),
        })
        response = read(InputOutput())
        json_response = response[0]
        response_data = json_response['data']
        self.assertEquals(200, response[1])
        self.assertEquals('success', json_response['status'])
        self.assertEquals({'numberResults': 2, 'start': 0, 'limit': 100}, json_response['pagination'])
        self.assertEquals({'id': 5, 'name': 'conor', 'email': 'cmancone1@example.com', 'age': 15}, response_data[0])
        self.assertEquals({'id': 8, 'name': 'ronoc', 'email': 'cmancone2@example.com', 'age': 25}, response_data[1])

        self.assertEquals({
            'wheres': [],
            'sorts': [{'column': 'email', 'direction': 'asc'}],
            'group_by_column': None,
            'joins': [],
            'limit_start': 0,
            'limit_length': 100,
            'selects': None,
            'table_name': 'models',
        }, Models.iterated[0])

    def test_configure(self):
        read = Read(self.di)
        read.configure({
            'models': self.models,
            'readable_columns': ['name'],
            'searchable_columns': ['name'],
            'where': ['age>5', 'age<10'],
            'default_sort_column': 'name',
            'default_sort_direction': 'desc',
            'default_limit': 50,
            'join': ['JOIN users ON users.id=model.id'],
            'group_by': 'id',
            'authentication': Public(),
        })
        response = read(InputOutput())
        json_response = response[0]
        response_data = json_response['data']
        self.assertEquals(200, response[1])
        self.assertEquals('success', json_response['status'])
        self.assertEquals(2, len(response_data))
        self.assertEquals({'id': 5, 'name': 'conor'}, response_data[0])
        self.assertEquals({'id': 8, 'name': 'ronoc'}, response_data[1])
        self.assertEquals({'numberResults': 2, 'start': 0, 'limit': 50}, json_response['pagination'])

        self.assertEquals({
            'wheres': [
                {'column': 'age', 'operator': '>', 'values': ['5'], 'parsed': 'age>?'},
                {'column': 'age', 'operator': '<', 'values': ['10'], 'parsed': 'age<?'},
            ],
            'sorts': [{'column': 'name', 'direction': 'desc'}],
            'group_by_column': 'id',
            'joins': ['JOIN users ON users.id=model.id'],
            'limit_start': 0,
            'limit_length': 50,
            'selects': None,
            'table_name': 'models',
        }, Models.iterated[0])

    def test_user_input(self):
        user_input = {
            'where': [{'column': 'email', 'value': 'bob@example.com'}],
            'sort': [{'column': 'age', 'direction': 'DESC'}],
            'start': 10,
            'limit': 5,
        }
        read = Read(self.di)
        read.configure({
            'models': self.models,
            'readable_columns': ['name', 'email', 'age'],
            'searchable_columns': ['email'],
            'where': ['age>5', 'age<10'],
            'default_sort_column': 'email',
            'authentication': Public(),
        })
        response = read(InputOutput(body=user_input))
        json_response = response[0]
        response_data = json_response['data']
        self.assertEquals(200, response[1])
        self.assertEquals('success', json_response['status'])
        self.assertEquals(2, len(response_data))
        self.assertEquals({'numberResults': 2, 'start': 10, 'limit': 5}, json_response['pagination'])
        self.assertEquals({
            'wheres': [
                {'column': 'age', 'operator': '>', 'values': ['5'], 'parsed': 'age>?'},
                {'column': 'age', 'operator': '<', 'values': ['10'], 'parsed': 'age<?'},
                {'column': 'email', 'operator': 'LIKE', 'values': ['%bob@example.com%'], 'parsed': 'email LIKE ?'},
            ],
            'sorts': [{'column': 'age', 'direction': 'DESC'}],
            'group_by_column': None,
            'joins': [],
            'limit_start': 10,
            'limit_length': 5,
            'selects': None,
            'table_name': 'models',
        }, Models.iterated[0])

    def test_output_map(self):
        read = Read(self.di)
        read.configure({
            'models': self.models,
            'readable_columns': ['name', 'email', 'age'],
            'searchable_columns': ['name'],
            'default_sort_column': 'email',
            'authentication': Public(),
            'output_map': lambda model: {'id': model.id, 'awesome': model.name},
        })
        response = read(InputOutput())
        json_response = response[0]
        response_data = json_response['data']
        self.assertEquals(200, response[1])
        self.assertEquals('success', json_response['status'])
        self.assertEquals({'numberResults': 2, 'start': 0, 'limit': 100}, json_response['pagination'])
        self.assertEquals({'id': 5, 'awesome': 'conor'}, response_data[0])
        self.assertEquals({'id': 8, 'awesome': 'ronoc'}, response_data[1])
