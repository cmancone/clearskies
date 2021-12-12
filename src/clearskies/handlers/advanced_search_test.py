import unittest
from .advanced_search import AdvancedSearch
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

class ReadTest(unittest.TestCase):
    def setUp(self):
        self.advanced_search = test({
            'handler_class': AdvancedSearch,
            'handler_config': {
                'model_class': User,
                'readable_columns': ['name', 'email', 'age'],
                'searchable_columns': ['name'],
                'default_sort_column': 'email',
                'authentication': Public(),
            }
        })
        self.users = self.advanced_search.build(User)
        self.users.create({'id': '1', 'name': 'ronoc', 'email': 'cmancone1@example.com', 'age': '6'})
        self.users.create({'id': '2', 'name': 'conor', 'email': 'cmancone2@example.com', 'age': '8'})
        self.users.create({'id': '5', 'name': 'conor', 'email': 'cmancone3@example.com', 'age': '15'})
        self.users.create({'id': '8', 'name': 'ronoc', 'email': 'cmancone4@example.com', 'age': '25'})
        self.users.create({'id': '12', 'name': 'ronoc', 'email': 'cmancone5@example.com', 'age': '35'})

    def test_simple_read(self):
        response = self.advanced_search()
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

    def test_fancy_search(self):
        response = self.advanced_search(body={
            'where': [
                {'column': 'name', 'operator': '=', 'value': 'ronoc'},
                {'column': 'age', 'operator': '<=', 'value': '25'},
            ]
        })
        json_response = response[0]
        response_data = json_response['data']
        self.assertEquals(200, response[1])
        self.assertEquals('success', json_response['status'])
        self.assertEquals({'numberResults': 2, 'start': 0, 'limit': 100}, json_response['pagination'])
        self.assertEquals({'id': '1', 'name': 'ronoc', 'email': 'cmancone1@example.com', 'age': 6}, response_data[0])
        self.assertEquals({'id': '8', 'name': 'ronoc', 'email': 'cmancone4@example.com', 'age': 25}, response_data[1])

    def test_doc(self):
        advanced_search = AdvancedSearch(StandardDependencies())
        advanced_search.configure({
            'model_class': User,
            'readable_columns': ['name', 'email', 'age'],
            'searchable_columns': ['name', 'email'],
            'default_sort_column': 'email',
            'authentication': Public(),
        })

        documentation = advanced_search.documentation()
        self.assertEquals(1, len(documentation))
        search_doc = documentation[0]

        self.assertEquals([''], [doc.relative_path for doc in documentation])
        self.assertEquals([['POST']], [doc.request_methods for doc in documentation])

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
