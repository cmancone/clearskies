import unittest
from .list import List
from ..column_types import String, Integer
from ..di import StandardDependencies
from ..authentication import Public, SecretBearer
from ..model import Model
from ..contexts import test
from collections import OrderedDict


class User(Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            ('id', {'class': String}),
            ('name', {'class': String}),
            ('email', {'class': String}),
            ('age', {'class': Integer}),
        ])

class ListTest(unittest.TestCase):
    def setUp(self):
        self.list = test({
            'handler_class': List,
            'handler_config': {
                'model_class': User,
                'readable_columns': ['name', 'email', 'age'],
                'searchable_columns': ['name'],
                'default_sort_column': 'email',
                'authentication': Public(),
            }
        })
        self.users = self.list.build(User)
        self.users.create({'id': '1', 'name': 'ronoc', 'email': 'cmancone1@example.com', 'age': '6'})
        self.users.create({'id': '2', 'name': 'conor', 'email': 'cmancone2@example.com', 'age': '8'})
        self.users.create({'id': '5', 'name': 'conor', 'email': 'cmancone3@example.com', 'age': '15'})
        self.users.create({'id': '8', 'name': 'ronoc', 'email': 'cmancone4@example.com', 'age': '25'})
        self.users.create({'id': '12', 'name': 'ronoc', 'email': 'cmancone5@example.com', 'age': '35'})

    def test_simple_list(self):
        response = self.list()
        json_response = response[0]
        response_data = json_response['data']
        self.assertEquals(200, response[1])
        self.assertEquals('success', json_response['status'])
        self.assertEquals({'numberResults': 5, 'start': 0, 'limit': 100}, json_response['pagination'])
        self.assertEquals({'id': '1', 'name': 'ronoc', 'email': 'cmancone1@example.com', 'age': 6}, response_data[0])
        self.assertEquals({'id': '2', 'name': 'conor', 'email': 'cmancone2@example.com', 'age': 8}, response_data[1])
        self.assertEquals({'id': '5', 'name': 'conor', 'email': 'cmancone3@example.com', 'age': 15}, response_data[2])
        self.assertEquals({'id': '8', 'name': 'ronoc', 'email': 'cmancone4@example.com', 'age': 25}, response_data[3])
        self.assertEquals({'id': '12', 'name': 'ronoc', 'email': 'cmancone5@example.com', 'age': 35}, response_data[4])

    def test_user_input(self):
        response = self.list(body={'sort': 'name', 'direction': 'desc'})
        json_response = response[0]
        response_data = json_response['data']
        self.assertEquals(200, response[1])
        self.assertEquals('success', json_response['status'])
        self.assertEquals({'numberResults': 5, 'start': 0, 'limit': 100}, json_response['pagination'])
        self.assertEquals({'id': '1', 'name': 'ronoc', 'email': 'cmancone1@example.com', 'age': 6}, response_data[0])
        self.assertEquals({'id': '8', 'name': 'ronoc', 'email': 'cmancone4@example.com', 'age': 25}, response_data[1])
        self.assertEquals({'id': '12', 'name': 'ronoc', 'email': 'cmancone5@example.com', 'age': 35}, response_data[2])
        self.assertEquals({'id': '2', 'name': 'conor', 'email': 'cmancone2@example.com', 'age': 8}, response_data[3])
        self.assertEquals({'id': '5', 'name': 'conor', 'email': 'cmancone3@example.com', 'age': 15}, response_data[4])

    def test_configure(self):
        list = test({
            'handler_class': List,
            'handler_config': {
                'model_class': User,
                'readable_columns': ['name'],
                'searchable_columns': ['name'],
                'where': ['age>5', 'age<10'],
                'default_sort_column': 'name',
                'default_sort_direction': 'desc',
                'default_limit': 50,
                'group_by': 'id',
                'authentication': Public(),
            }
        })
        users = list.build(User)
        users.create({'id': '1', 'name': 'conor', 'email': 'cmancone1@example.com', 'age': '6'})
        users.create({'id': '2', 'name': 'ronoc', 'email': 'cmancone1@example.com', 'age': '8'})
        users.create({'id': '5', 'name': 'conor', 'email': 'cmancone1@example.com', 'age': '15'})
        users.create({'id': '8', 'name': 'ronoc', 'email': 'cmancone2@example.com', 'age': '25'})
        users.create({'id': '10', 'name': 'ronoc', 'email': 'cmancone2@example.com', 'age': '30'})

        response = list()
        json_response = response[0]
        response_data = json_response['data']
        self.assertEquals(200, response[1])
        self.assertEquals('success', json_response['status'])
        self.assertEquals(2, len(response_data))
        self.assertEquals({'id': '2', 'name': 'ronoc'}, response_data[0])
        self.assertEquals({'id': '1', 'name': 'conor'}, response_data[1])
        self.assertEquals({'numberResults': 2, 'start': 0, 'limit': 50}, json_response['pagination'])

    def test_output_map(self):
        list = test({
            'handler_class': List,
            'handler_config': {
                'model_class': User,
                'readable_columns': ['name', 'email', 'age'],
                'searchable_columns': ['name'],
                'default_sort_column': 'email',
                'authentication': Public(),
                'output_map': lambda model: {'id': model.id, 'awesome': model.name},
            }
        })
        users = list.build(User)
        users.create({'id': '1', 'name': 'ronoc', 'email': 'cmancone1@example.com', 'age': '6'})
        users.create({'id': '2', 'name': 'conor', 'email': 'cmancone2@example.com', 'age': '8'})

        response = list()
        json_response = response[0]
        response_data = json_response['data']
        self.assertEquals(200, response[1])
        self.assertEquals('success', json_response['status'])
        self.assertEquals({'numberResults': 2, 'start': 0, 'limit': 100}, json_response['pagination'])
        self.assertEquals({'id': '1', 'awesome': 'ronoc'}, response_data[0])
        self.assertEquals({'id': '2', 'awesome': 'conor'}, response_data[1])

    def test_doc(self):
        list = List(StandardDependencies())
        list.configure({
            'model_class': User,
            'readable_columns': ['name', 'email', 'age'],
            'searchable_columns': ['name', 'email'],
            'default_sort_column': 'email',
            'authentication': Public(),
        })

        documentation = list.documentation(include_search=True)
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
