import unittest
from unittest.mock import MagicMock, call
from .base import Base
from .exceptions import ClientError, InputError
from ..di import StandardDependencies
from ..authentication import public, Authorization
from ..security_headers import hsts, cors
def raise_exception(exception):
    raise exception
class Handle(Base):
    _global_configuration_defaults = {
        'age': 10,
        'global': 'yes',
        'response_headers': None,
        'authentication': None,
        'authorization': None,
        'security_headers': None,
    }
    _configuration_defaults = {
        'age': 5,
        'is_awesome': True,
        'test': 'value',
        'internal_casing': '',
        'external_casing': '',
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
class RejectAuth(Authorization):
    def gate(self, authorization_data, input_output):
        return False
class AllowAuth(Authorization):
    def gate(self, authorization_data, input_output):
        return True
class BaseTest(unittest.TestCase):
    def setUp(self):
        self.di = StandardDependencies()
        self.reflect_output = type(
            '', (), {
                'respond': lambda message, status_code: (message, status_code),
                'set_header': MagicMock(),
                'get_authorization_data': lambda: {},
            }
        )

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
            "\"Attempt to set unknown configuration setting 'whatev' for handler 'Handle'\"", str(context.exception)
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
            'input_errors': {},
        }, data)
        self.assertEquals(200, code)

    def test_pagination(self):
        handle = Handle(self.di)
        handle.configure({'authentication': public()})
        (data,
         code) = handle.success(self.reflect_output, [1, 2, 3], number_results=3, limit=10, next_page={'start': 1})
        self.assertEquals({
            'status': 'success',
            'error': '',
            'data': [1, 2, 3],
            'pagination': {
                'number_results': 3,
                'limit': 10,
                'next_page': {
                    'start': 1
                }
            },
            'input_errors': {},
        }, data)
        self.assertEquals(200, code)

    def test_error(self):
        handle = Handle(self.di)
        handle.configure({'authentication': public()})
        (data, code) = handle.error(self.reflect_output, 'bah', 400)
        self.assertEquals({
            'status': 'client_error',
            'error': 'bah',
            'data': [],
            'pagination': {},
            'input_errors': {},
        }, data)
        self.assertEquals(400, code)

    def test_input_errors(self):
        handle = Handle(self.di)
        handle.configure({'authentication': public()})
        (data, code) = handle.input_errors(self.reflect_output, {'age': 'required', 'date': 'tomorrow'})
        self.assertEquals({
            'status': 'input_errors',
            'error': '',
            'data': [],
            'pagination': {},
            'input_errors': {
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
            'input_errors': {},
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
            'status': 'client_error',
            'error': 'sup',
            'data': [],
            'pagination': {},
            'input_errors': {},
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
            'status': 'input_errors',
            'error': '',
            'data': [],
            'pagination': {},
            'input_errors': {
                'id': 'required'
            },
        }, data)
        self.assertEquals(200, code)

    def test_security_headers(self):
        authentication = type('', (), {'authenticate': MagicMock(return_value=True)})
        handle = Handle(self.di)
        handle.configure({'authentication': authentication, 'security_headers': hsts()})
        (data, code) = handle.success(self.reflect_output, [1, 2, 3])
        self.assertEquals(200, code)
        self.reflect_output.set_header.assert_called_with('strict-transport-security', 'max-age=31536000 ;')

    def test_cors(self):
        authentication = type(
            '', (), {
                'authenticate': MagicMock(return_value=True),
                'set_headers_for_cors': lambda self, cors: cors.add_header('Authorization')
            }
        )
        handle = Handle(self.di)
        handle.configure({'authentication': authentication, 'security_headers': cors(origin='*')})
        (data, code) = handle.cors(self.reflect_output)
        self.assertEquals(200, code)
        self.assertEquals('', data)
        self.reflect_output.set_header.assert_has_calls([
            call('access-control-allow-origin', '*'),
            call('access-control-allow-headers', 'Authorization'),
        ])

    def test_authn(self):
        authentication = type('', (), {'authenticate': MagicMock(return_value=False)})
        handle = Handle(self.di)
        handle.configure({
            'authentication': authentication,
        })
        (data, code) = handle(self.reflect_output)
        self.assertEquals({
            'status': 'client_error',
            'error': 'Not Authenticated',
            'data': [],
            'pagination': {},
            'input_errors': {},
        }, data)
        self.assertEquals(401, code)

    def test_authz_gate_reject(self):
        authentication = type('', (), {'authenticate': MagicMock(return_value=True)})
        handle = Handle(self.di)
        handle.configure({'authentication': authentication, 'authorization': RejectAuth()})
        (data, code) = handle(self.reflect_output)
        self.assertEquals({
            'status': 'client_error',
            'error': 'Not Authorized',
            'data': [],
            'pagination': {},
            'input_errors': {},
        }, data)
        self.assertEquals(403, code)

    def test_authz_gate_allow(self):
        authentication = type('', (), {'authenticate': MagicMock(return_value=True)})
        handle = Handle(self.di)
        handle.configure({'authentication': authentication, 'authorization': AllowAuth()})
        (data, code) = handle(self.reflect_output)
        self.assertEquals({
            'status': 'success',
            'error': '',
            'data': [1, 2, 3],
            'pagination': {},
            'input_errors': {},
        }, data)
        self.assertEquals(200, code)
