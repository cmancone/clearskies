import unittest
from unittest.mock import MagicMock, call
from .base import Base
from .request_method_routing import RequestMethodRouting
from .exceptions import ClientError, InputError
from ..mocks import InputOutput
from ..binding_specs import BindingSpec
import pinject
from ..authentication import Public


class MockBindingSpec(BindingSpec):
    _input_output = None
    _authentication = None

    def __init__(self, input_output, authentication):
        self._input_output = input_output
        self._authentication = authentication

    def provide_input_output(self):
        return self._input_output

    def provide_authentication(self):
        return self._authentication

class Handle(Base):
    _configuration_defaults = {
        'age': 5,
    }

    def handle(self):
        return self.success([1, 2, 3])

class Router(RequestMethodRouting):
    def __init__(self, input_output, authentication, object_graph):
        super().__init__(input_output, authentication, object_graph)

    def method_handler_map(self):
        return {
            'GET': Handle,
            'POST': Handle,
        }

class RequestMethodRoutingTest(unittest.TestCase):
    _input_output = None
    _object_graph = None

    def setUp(self):
        self._input_output = InputOutput(request_method='POST')
        self._object_graph = pinject.new_object_graph(binding_specs=[
            MockBindingSpec(self._input_output, Public())
        ])

    def test_route(self):
        self.assertTrue(True)
        handle = Router(self._input_output, Public(), self._object_graph)
        handle.configure({})
        result = handle()
        self.assertEquals([1, 2, 3], result[0]['data'])
