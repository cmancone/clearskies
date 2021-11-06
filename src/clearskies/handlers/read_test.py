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
                {'table': '', 'column': 'age', 'operator': '>', 'values': ['5'], 'parsed': 'age>%s'},
                {'table': '', 'column': 'age', 'operator': '<', 'values': ['10'], 'parsed': 'age<%s'},
            ],
            'sorts': [{'column': 'name', 'direction': 'desc'}],
            'group_by_column': 'id',
            'joins': [
                {
                    'type': 'INNER',
                    'table': 'users',
                    'left_table': 'model',
                    'left_column': 'id',
                    'right_table': 'users',
                    'right_column': 'id',
                    'raw': 'JOIN users ON users.id=model.id',
                    'alias': '',
                },
            ],
            'limit_start': 0,
            'limit_length': 50,
            'selects': None,
            'table_name': 'models',
        }, Models.iterated[0])

    def test_user_input(self):
        user_input = {
            'where': [{'table': '', 'column': 'email', 'value': 'bob@example.com'}],
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
                {'table': '', 'column': 'age', 'operator': '>', 'values': ['5'], 'parsed': 'age>%s'},
                {'table': '', 'column': 'age', 'operator': '<', 'values': ['10'], 'parsed': 'age<%s'},
                {'table': '', 'column': 'email', 'operator': 'LIKE', 'values': ['%bob@example.com%'], 'parsed': 'email LIKE %s'},
            ],
            'sorts': [{'column': 'age', 'direction': 'DESC'}],
            'group_by_column': None,
            'joins': [],
            'limit_start': 10,
            'limit_length': 5,
            'selects': None,
            'table_name': 'models',
        }, Models.iterated[0])

    def test_query_parameters(self):
        user_input = {
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
        response = read(InputOutput(body=user_input, query_parameters={'email': 'bob@example.com'}))
        json_response = response[0]
        response_data = json_response['data']
        self.assertEquals(200, response[1])
        self.assertEquals('success', json_response['status'])
        self.assertEquals(2, len(response_data))
        self.assertEquals({'numberResults': 2, 'start': 10, 'limit': 5}, json_response['pagination'])
        self.assertEquals({
            'wheres': [
                {'table': '', 'column': 'age', 'operator': '>', 'values': ['5'], 'parsed': 'age>%s'},
                {'table': '', 'column': 'age', 'operator': '<', 'values': ['10'], 'parsed': 'age<%s'},
                {'table': '', 'column': 'email', 'operator': 'LIKE', 'values': ['%bob@example.com%'], 'parsed': 'email LIKE %s'},
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

    def test_doc(self):
        read = Read(self.di)
        read.configure({
            'models': self.models,
            'readable_columns': ['name', 'email', 'age'],
            'searchable_columns': ['name', 'email'],
            'default_sort_column': 'email',
            'authentication': Public(),
        })

        documentation = read.documentation(include_search=True)
        all_doc = documentation[0]
        resource_doc = documentation[1]
        search_doc = documentation[2]

        self.assertEquals(3, len(documentation))
        self.assertEquals(['', '{id}', 'search'], [doc.relative_path for doc in documentation])
        self.assertEquals([['GET'], ['GET'], ['POST']], [doc.request_methods for doc in documentation])

        # Check our 'all' endpoint which returns all records
        self.assertEquals(2, len(all_doc.responses))
        self.assertEquals([200, 400], [response.status for response in all_doc.responses])
        self.assertEquals(
            ['status', 'data', 'pagination', 'error', 'inputErrors'],
            [schema.name for schema in all_doc.responses[0].schema.children]
        )
        data_response_properties = all_doc.responses[0].schema.children[1].item_definition.children
        self.assertEquals(['id', 'name', 'email', 'age'], [prop.name for prop in data_response_properties])
        self.assertEquals(['string', 'string', 'string', 'integer'], [prop._type for prop in data_response_properties])
        self.assertEquals(
            ['name', 'email', 'start', 'limit', 'sort', 'direction'],
            [param.definition.name for param in all_doc.parameters]
        )

        # then check our 'resource' endpoint which returns a particular record
        self.assertEquals(2, len(resource_doc.responses))
        self.assertEquals([200, 404], [response.status for response in resource_doc.responses])
        self.assertEquals(
            ['status', 'data', 'pagination', 'error', 'inputErrors'],
            [schema.name for schema in resource_doc.responses[0].schema.children]
        )
        data_response_properties = resource_doc.responses[0].schema.children[1].children
        self.assertEquals(['id', 'name', 'email', 'age'], [prop.name for prop in data_response_properties])
        self.assertEquals(['string', 'string', 'string', 'integer'], [prop._type for prop in data_response_properties])
        self.assertEquals(['id'], [param.definition.name for param in resource_doc.parameters])

        # Check our 'search' endpoint which returns all records with fancy search options
        self.assertEquals(2, len(search_doc.responses))
        self.assertEquals([200, 400], [response.status for response in search_doc.responses])
        self.assertEquals(
            ['status', 'data', 'pagination', 'error', 'inputErrors'],
            [schema.name for schema in search_doc.responses[0].schema.children]
        )
        data_response_properties = search_doc.responses[0].schema.children[1].item_definition
        self.assertEquals(['id', 'name', 'email', 'age'], [prop.name for prop in data_response_properties.children])
        self.assertEquals(['string', 'string', 'string', 'integer'], [prop._type for prop in data_response_properties.children])
        self.assertEquals(
            ['where', 'sort', 'start', 'limit'],
            [param.definition.name for param in search_doc.parameters]
        )
        self.assertEquals(3, len(search_doc.parameters[0].definition.item_definition.children))
        self.assertEquals(
            ['column', 'operator', 'value'],
            [child.name for child in search_doc.parameters[0].definition.item_definition.children]
        )
        self.assertEquals(
            ['name', 'email'],
            search_doc.parameters[0].definition.item_definition.children[0].values
        )
