import unittest
from .callable import Callable
from ..column_types import String, Integer
from ..input_requirements import Required, MaximumLength
from ..authentication import Public, SecretBearer
from ..model import Model
from ..contexts import test
from collections import OrderedDict
from unittest.mock import MagicMock
from ..di import StandardDependencies


class User(Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            ('name', {'class': String, 'input_requirements': [Required]}),
            ('email', {'class': String, 'input_requirements': [Required, (MaximumLength, 15)]}),
            ('age', {'class': Integer}),
        ])

def return_request_data(request_data=None):
    return request_data

def return_contstant():
    return 'CONSTANT!'

class CallableTest(unittest.TestCase):
    def test_without_schema(self):
        callable_handler = test({
            'handler_class': Callable,
            'handler_config': {
                'callable': return_contstant,
                'authentication': Public(),
            }
        })
        response = callable_handler()
        self.assertEquals(200, response[1])
        self.assertEquals('CONSTANT!', response[0]['data'])

    def test_with_schema(self):
        callable_handler = test({
            'handler_class': Callable,
            'handler_config': {
                'callable': return_request_data,
                'authentication': Public(),
                'schema': User,
            }
        })
        response = callable_handler(body={'name': 'hey', 'email': 'sup@sup.com', 'age': 10})
        self.assertEquals(200, response[1])
        self.assertEquals({'name': 'hey', 'email': 'sup@sup.com', 'age': 10}, response[0]['data'])

    def test_with_input_errors(self):
        test_callable = MagicMock(return_value=None)
        callable_handler = test({
            'handler_class': Callable,
            'handler_config': {
                'callable': test_callable,
                'authentication': Public(),
                'schema': User,
            }
        })
        response = callable_handler(body={'name': 'hey', 'age': 'asfd', 'bob': 'sup'})
        self.assertEquals(200, response[1])
        self.assertEquals({
            'bob': "Input column 'bob' is not an allowed column",
            'email': "'email' is required.",
            'age': 'age must be an integer',
        }, response[0]['input_errors'])
        self.assertEquals([], response[0]['data'])
        test_callable.assert_not_called()

    def test_with_selectable_columns(self):
        callable_handler = test({
            'handler_class': Callable,
            'handler_config': {
                'callable': return_request_data,
                'authentication': Public(),
                'schema': User,
                'writeable_columns': ['name', 'age'],
            }
        })
        response = callable_handler(body={'name': 'hey', 'age': 10})
        self.assertEquals(200, response[1])
        self.assertEquals({
            'name': 'hey',
            'age': 10,
        }, response[0]['data'])

    def test_with_mapping(self):
        callable_handler = test({
            'handler_class': Callable,
            'handler_config': {
                'callable': return_request_data,
                'authentication': Public(),
                'schema': User,
                'internal_casing': 'snake_case',
                'external_casing': 'TitleCase',
            }
        })
        response = callable_handler(body={'Name': 'hey', 'Age': 10, 'Email': 'bob@bob.com'})
        self.assertEquals(200, response[1])
        self.assertEquals({
            'name': 'hey',
            'age': 10,
            'email': 'bob@bob.com',
        }, response[0]['Data'])

    def test_doc(self):
        callable_handler = Callable(StandardDependencies())
        callable_handler.configure({
            'callable': return_contstant,
            'authentication': Public(),
            'schema': User,
            'internal_casing': 'snake_case',
            'external_casing': 'TitleCase',
            'writeable_columns': ['name', 'age']
        })

        documentation = callable_handler.documentation()[0]

        self.assertEquals(2, len(documentation.parameters))
        self.assertEquals(['Name', 'Age'], [param.definition.name for param in documentation.parameters])
        self.assertEquals([True, False], [param.required for param in documentation.parameters])

        self.assertEquals(2, len(documentation.responses))
        self.assertEquals([200, 404], [response.status for response in documentation.responses])
        success_response = documentation.responses[0]
        self.assertEquals(
            ['Status', 'Data', 'Pagination', 'Error', 'InputErrors'],
            [schema.name for schema in success_response.schema.children]
        )
        data_response_properties = success_response.schema.children[1].children
        self.assertEquals([], [prop.name for prop in data_response_properties])
        self.assertEquals([], [prop._type for prop in data_response_properties])
