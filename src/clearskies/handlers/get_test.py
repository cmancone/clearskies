import unittest
from .get import Get
from ..column_types import String, Integer
from ..input_requirements import Required, MaximumLength
from ..authentication import Public, SecretBearer, Authorization
from ..di import StandardDependencies
from .. import Model
from collections import OrderedDict
from ..contexts import test
class User(Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            ('id', {
                'class': String
            }),    # otherwise we'll use a UUID for the id, so I can't predict it
            ('name', {
                'class': String,
                'input_requirements': [Required]
            }),
            ('email', {
                'class': String,
                'input_requirements': [Required, (MaximumLength, 15)]
            }),
            ('age', {
                'class': Integer
            }),
        ])
class FilterAuth(Authorization):
    def filter_models(self, models, authorization_data, input_output):
        email = authorization_data.get('email')
        return models.where(f'email={email}')
class GetTest(unittest.TestCase):
    def setUp(self):
        self.get = test({
            'handler_class': Get,
            'handler_config': {
                'model_class': User,
                'readable_columns': ['name', 'email', 'age'],
                'authentication': Public(),
            }
        })
        self.users = self.get.build(User)
        self.users.create({'id': '5', 'name': 'bob', 'email': 'bob@example.com', 'age': '25'})

    def test_get(self):
        response = self.get(routing_data={'id': '5'})
        response_data = response[0]['data']
        self.assertEquals(200, response[1])
        self.assertEquals('5', response_data['id'])
        self.assertEquals(25, response_data['age'])
        self.assertEquals('bob', response_data['name'])
        self.assertEquals('bob@example.com', response_data['email'])

    def test_authz(self):
        get = test({
            'handler_class': Get,
            'handler_config': {
                'model_class': User,
                'readable_columns': ['name', 'email', 'age'],
                'authentication': Public(),
                'authorization': FilterAuth(),
            },
        })
        users = get.build(User)
        users.create({'id': '5', 'name': 'bob', 'email': 'bob@example.com', 'age': '25'})
        users.create({'id': '6', 'name': 'bob', 'email': 'bob2@example.com', 'age': '25'})
        response = get(routing_data={'id': '5'}, authorization_data={'email': 'bob@example.com'})
        response_data = response[0]['data']
        self.assertEquals(200, response[1])
        self.assertEquals('5', response_data['id'])
        self.assertEquals(25, response_data['age'])
        self.assertEquals('bob', response_data['name'])
        self.assertEquals('bob@example.com', response_data['email'])

        # double check that if we find nothing for a non-match
        response = get(routing_data={'id': '6'}, authorization_data={'email': 'bob@example.com'})
        self.assertEquals(404, response[1])

    def test_not_found(self):
        response = self.get(routing_data={'id': '10'})
        self.assertEquals(404, response[1])
        self.assertEquals({
            'status': 'client_error',
            'error': 'Not Found',
            'data': [],
            'pagination': {},
            'input_errors': {}
        }, response[0])

    def test_doc(self):
        get = Get(StandardDependencies())
        get.configure({
            'model': self.users,
            'readable_columns': ['name', 'email', 'age'],
            'authentication': Public(),
        })

        documentation = get.documentation()[0]

        self.assertEquals('{id}', documentation.relative_path)

        self.assertEquals(0, len(documentation.parameters))
        self.assertEquals(2, len(documentation.responses))
        self.assertEquals([200, 404], [response.status for response in documentation.responses])
        success_response = documentation.responses[0]
        self.assertEquals(['status', 'data', 'pagination', 'error', 'input_errors'],
                          [schema.name for schema in success_response.schema.children])
        data_response_properties = success_response.schema.children[1].children
        self.assertEquals(['id', 'name', 'email', 'age'], [prop.name for prop in data_response_properties])
        self.assertEquals(['string', 'string', 'string', 'integer'], [prop._type for prop in data_response_properties])
