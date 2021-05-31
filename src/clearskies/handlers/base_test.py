import unittest
from unittest.mock import MagicMock, call
from .base import Base
from .exceptions import ClientError, InputError
from ..di import StandardDependencies
from ..authentication import public


def raise_exception(exception):
    raise exception

class Handle(Base):
    _global_configuration_defaults = {
        'age': 10,
        'global': 'yes',
        'response_headers': None,
        'authentication': None,
    }
    _configuration_defaults = {
        'age': 5,
        'is_awesome': True,
        'test': 'value',
    }

    def _finalize_configuration(self, configuration):
        return {
            **super()._finalize_configuration(configuration),
            'hey': 'sup',
        }

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        if 'bah' in configuration:
            raise KeyError("BAH!")

    def handle(self, input_output):
        return self.success(input_output, [1, 2, 3])

class BaseTest(unittest.TestCase):
    def setUp(self):
        self.di = StandardDependencies()
        self.reflect_output = type('', (), {
            'respond': lambda message, status_code: (message, status_code),
        })

    def test_configure(self):
        handle = Handle(self.di)
        handle.configure({'test': 'okay', 'authentication': public()})
        self.assertEquals('okay', handle.configuration('test'))
        self.assertEquals(5, handle.configuration('age'))
        self.assertEquals('yes', handle.configuration('global'))
        self.assertEquals(True, handle.configuration('is_awesome'))
        self.assertRaises(KeyError, lambda: handle.configuration('sup'))

    def test_require_config(self):
        handle = Handle(self.di)
        self.assertRaises(ValueError, lambda: handle.configuration('age'))

    def test_invalid_configuration(self):
        handle = Handle(self.di)
        handle.configure({'authentication': public()})
        with self.assertRaises(KeyError) as context:
            handle.configure({'whatev': 'hey', 'authentication': public()})
        self.assertEquals(
            "\"Attempt to set unkown configuration setting 'whatev' for handler 'Handle'\"",
            str(context.exception)
        )

    def test_success(self):
        handle = Handle(self.di)
        handle.configure({'authentication': public()})
        (data, code) = handle.success(self.reflect_output, [1, 2, 3])
        self.assertEquals({
            'status': 'success',
            'error': '',
            'data': [1, 2, 3],
            'pagination': {},
            'inputErrors': {},
        }, data)
        self.assertEquals(200, code)

    def test_pagination(self):
        handle = Handle(self.di)
        handle.configure({'authentication': public()})
        (data, code) = handle.success(self.reflect_output, [1, 2, 3], number_results=3, limit=10, start=1)
        self.assertEquals({
            'status': 'success',
            'error': '',
            'data': [1, 2, 3],
            'pagination': {'numberResults': 3, 'limit': 10, 'start': 1},
            'inputErrors': {},
        }, data)
        self.assertEquals(200, code)

    def test_error(self):
        handle = Handle(self.di)
        handle.configure({'authentication': public()})
        (data, code) = handle.error(self.reflect_output, 'bah', 400)
        self.assertEquals({
            'status': 'clientError',
            'error': 'bah',
            'data': [],
            'pagination': {},
            'inputErrors': {},
        }, data)
        self.assertEquals(400, code)

    def test_input_errors(self):
        handle = Handle(self.di)
        handle.configure({'authentication': public()})
        (data, code) = handle.input_errors(self.reflect_output, {'age': 'required', 'date': 'tomorrow'})
        self.assertEquals({
            'status': 'inputErrors',
            'error': '',
            'data': [],
            'pagination': {},
            'inputErrors': {
                'age': 'required',
                'date': 'tomorrow',
            },
        }, data)
        self.assertEquals(200, code)

    def test_handle(self):
        authentication = type('', (), {'authenticate': MagicMock(return_value=True)})
        handle = Handle(self.di)
        handle.configure({
            'authentication': authentication,
        })
        (data, code) = handle(self.reflect_output)
        self.assertEquals({
            'status': 'success',
            'error': '',
            'data': [1, 2, 3],
            'pagination': {},
            'inputErrors': {},
        }, data)
        self.assertEquals(200, code)
        authentication.authenticate.assert_called_with(self.reflect_output)

    def test_error(self):
        authentication = type('', (), {'authenticate': MagicMock(return_value=True)})
        handle = Handle(self.di)
        handle.configure({
            'authentication': authentication,
        })
        handle.handle = lambda input_output: raise_exception(ClientError('sup'))
        (data, code) = handle(self.reflect_output)
        self.assertEquals({
            'status': 'clientError',
            'error': 'sup',
            'data': [],
            'pagination': {},
            'inputErrors': {},
        }, data)
        self.assertEquals(400, code)

    def test_input_error(self):
        authentication = type('', (), {'authenticate': MagicMock(return_value=True)})
        handle = Handle(self.di)
        handle.configure({
            'authentication': authentication,
        })
        handle.handle = lambda input_output: raise_exception(InputError({'id': 'required'}))
        (data, code) = handle(self.reflect_output)
        self.assertEquals({
            'status': 'inputErrors',
            'error': '',
            'data': [],
            'pagination': {},
            'inputErrors': {'id': 'required'},
        }, data)
        self.assertEquals(200, code)
