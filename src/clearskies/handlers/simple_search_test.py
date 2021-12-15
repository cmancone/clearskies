import unittest
from .simple_search import SimpleSearch
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

class SimpleSearchTest(unittest.TestCase):
    def setUp(self):
        self.simple_search = test({
            'handler_class': SimpleSearch,
            'handler_config': {
                'model_class': User,
                'readable_columns': ['name', 'email', 'age'],
                'searchable_columns': ['name', 'email'],
                'default_sort_column': 'email',
                'authentication': Public(),
            }
        })
        self.users = self.simple_search.build(User)
        self.users.create({'id': '1', 'name': 'ronoc', 'email': 'cmancone1@example.com', 'age': '6'})
        self.users.create({'id': '2', 'name': 'conor', 'email': 'cmancone2@example.com', 'age': '8'})
        self.users.create({'id': '5', 'name': 'conor', 'email': 'cmancone3@example.com', 'age': '15'})
        self.users.create({'id': '8', 'name': 'ronoc', 'email': 'cmancone4@example.com', 'age': '25'})
        self.users.create({'id': '12', 'name': 'ronoc', 'email': 'cmancone5@example.com', 'age': '35'})

        self.simple_search_with_wheres = test({
            'handler_class': SimpleSearch,
            'handler_config': {
                'model_class': User,
                'readable_columns': ['name', 'email', 'age'],
                'searchable_columns': ['name', 'email'],
                'where': ['age>5', 'age<10'],
                'default_sort_column': 'name',
                'default_sort_direction': 'desc',
                'group_by': 'id',
                'authentication': Public(),
            }
        })
        self.users_with_wheres = self.simple_search_with_wheres.build(User)
        self.users_with_wheres.create({'id': '1', 'name': 'conor', 'email': 'cmancone1@example.com', 'age': '6'})
        self.users_with_wheres.create({'id': '2', 'name': 'ronoc', 'email': 'cmancone1@example.com', 'age': '8'})
        self.users_with_wheres.create({'id': '5', 'name': 'conor', 'email': 'cmancone1@example.com', 'age': '15'})
        self.users_with_wheres.create({'id': '8', 'name': 'ronoc', 'email': 'cmancone2@example.com', 'age': '25'})
        self.users_with_wheres.create({'id': '10', 'name': 'ronoc', 'email': 'cmancone2@example.com', 'age': '30'})
        self.users_with_wheres.create({'id': '11', 'name': 'ronoc', 'email': 'cmancone3@example.com', 'age': '7'})
        self.users_with_wheres.create({'id': '12', 'name': 'conor', 'email': 'cmancone4@example.com', 'age': '9'})

    def test_simple_read(self):
        response = self.simple_search()
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

    def test_configure(self):
        response = self.simple_search_with_wheres()
        json_response = response[0]
        response_data = json_response['data']
        self.assertEquals(200, response[1])
        self.assertEquals('success', json_response['status'])
        self.assertEquals(4, len(response_data))
        self.assertEquals({'id': '2', 'name': 'ronoc', 'email': 'cmancone1@example.com', 'age': 8}, response_data[0])
        self.assertEquals({'id': '11', 'name': 'ronoc', 'email': 'cmancone3@example.com', 'age': 7}, response_data[1])
        self.assertEquals({'id': '1', 'name': 'conor', 'email': 'cmancone1@example.com', 'age': 6}, response_data[2])
        self.assertEquals({'id': '12', 'name': 'conor', 'email': 'cmancone4@example.com', 'age': 9}, response_data[3])
        self.assertEquals({'numberResults': 4, 'start': 0, 'limit': 100}, json_response['pagination'])

    def test_user_input(self):
        response = self.simple_search(query_parameters={
            'email': 'cmancone3@example.com',
        })
        json_response = response[0]
        response_data = json_response['data']
        self.assertEquals(200, response[1])
        self.assertEquals('success', json_response['status'])
        self.assertEquals(1, len(response_data))
        self.assertEquals({'numberResults': 1, 'start': 0, 'limit': 100}, json_response['pagination'])
        self.assertEquals({'id': '5', 'name': 'conor', 'email': 'cmancone3@example.com', 'age': 15}, response_data[0])

    def test_user_input_with_config(self):
        response = self.simple_search_with_wheres(
            query_parameters={
                'sort': 'name',
                'direction': 'asc',
            },
            body={
                'email': 'cmancone1@example.com',
            }
        )
        json_response = response[0]
        response_data = json_response['data']
        self.assertEquals(200, response[1])
        self.assertEquals('success', json_response['status'])
        self.assertEquals(2, len(response_data))
        self.assertEquals({'numberResults': 2, 'start': 0, 'limit': 100}, json_response['pagination'])
        self.assertEquals({'id': '1', 'name': 'conor', 'email': 'cmancone1@example.com', 'age': 6}, response_data[0])
        self.assertEquals({'id': '2', 'name': 'ronoc', 'email': 'cmancone1@example.com', 'age': 8}, response_data[1])

    def test_doc(self):
        simple_search = SimpleSearch(StandardDependencies())
        simple_search.configure({
            'model_class': User,
            'readable_columns': ['name', 'email', 'age'],
            'searchable_columns': ['name', 'email'],
            'default_sort_column': 'email',
            'authentication': Public(),
        })

        documentation = simple_search.documentation()
        all_doc = documentation[0]
        self.assertEquals(1, len(documentation))

        self.assertEquals([''], [doc.relative_path for doc in documentation])
        self.assertEquals([['GET']], [doc.request_methods for doc in documentation])

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
            ['start', 'limit', 'sort', 'direction', 'name', 'email', 'name', 'email'],
            [param.definition.name for param in all_doc.parameters]
        )
        self.assertEquals(
            ['url_parameter', 'url_parameter', 'url_parameter', 'url_parameter', 'url_parameter', 'url_parameter', 'json_body', 'json_body'],
            [param.location for param in all_doc.parameters]
        )
