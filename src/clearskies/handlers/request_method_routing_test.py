import unittest
from unittest.mock import MagicMock, call
from .base import Base
from .request_method_routing import RequestMethodRouting
from .exceptions import ClientError, InputError
from ..mocks import InputOutput
from ..authentication import Public
from ..di import StandardDependencies


class Handle(Base):
    _configuration_defaults = {
        'age': 5,
    }

    def handle(self, input_output):
        return self.success(input_output, self.configuration('age'))

class Router(RequestMethodRouting):
    def __init__(self, di):
        super().__init__(di)

    def method_handler_map(self):
        return {
            'GET': Handle,
            'POST': Handle,
        }

class RequestMethodRoutingTest(unittest.TestCase):
    _input_output = None
    di = None

    def setUp(self):
        self._input_output = InputOutput(request_method='POST')
        self.di = StandardDependencies(bindings={
            'input_output': self._input_output,
        })

    def test_route(self):
        handle = self.di.build(Router)
        handle.configure({'authentication': Public()})
        result = handle(self._input_output)
        self.assertEquals(5, result[0]['data'])

    def test_route_non_method(self):
        self._input_output.set_request_method('OPTIONS')
        handle = self.di.build(Router)
        handle.configure({'authentication': Public()})
        result = handle(self._input_output)
        self.assertEquals(400, result[1])
        self.assertEquals('clientError', result[0]['status'])
        self.assertEquals('Invalid request method', result[0]['error'])

    def test_can_configure(self):
        handle = self.di.build(Router)
        handle.configure({'age': '10', 'authentication': Public()})
        self.assertEquals('10', handle.configuration('age'))

    def test_configure_errors(self):
        handle = self.di.build(Router)
        with self.assertRaises(KeyError) as context:
            handle.configure({'bob': 'sup', 'authentication': Public()})
        self.assertEquals(
            "\"Attempt to set unkown configuration setting 'bob' for handler 'Router'\"",
            str(context.exception)
        )
