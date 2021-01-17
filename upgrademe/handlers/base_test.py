import unittest
from unittest.mock import MagicMock, call
from .base import Base


class Handle(Base):
    _global_configuration_defaults = {
        'age': 10,
        'global': 'yes',
    }
    _configuration_defaults = {
        'age': 5,
        'is_awesome': True,
        'test': 'value',
    }

    def _finalize_configuration(self, configuration):
        return {
            **configuration,
            'hey': 'sup',
        }

    def _check_configuration(self, configuration):
        if 'bah' in configuration:
            raise KeyError("BAH!")

    def handle(self):
        return self.success([1, 2, 3])

class BaseTest(unittest.TestCase):
    def test_configure(self):
        handle = Handle('request', 'authentication')
        handle.configure({'test': 'okay'})
        self.assertEquals('okay', handle.configuration('test'))
        self.assertEquals(5, handle.configuration('age'))
        self.assertEquals('yes', handle.configuration('global'))
        self.assertEquals(True, handle.configuration('is_awesome'))
        self.assertRaises(KeyError, lambda: handle.configuration('sup'))

    def test_require_config(self):
        handle = Handle('request', 'authentication')
        self.assertRaises(ValueError, lambda: handle.configuration('age'))

    def test_invalid_configuration(self):
        handle = Handle('request', 'authentication')
        with self.assertRaises(KeyError) as context:
            handle.configure({'whatev': 'hey'})
        self.assertEquals(
            "\"Attempt to set unkown configuration setting 'whatev' for handler 'Handle'\"",
            str(context.exception)
        )

    def test_success(self):
        handle = Handle('request', 'authentication')
        (data, code) = handle.success([1, 2, 3])
        self.assertEquals({
            'status': 'success',
            'error': '',
            'data': [1, 2, 3],
            'pagination': {},
            'inputErrors': {},
        }, data)
        self.assertEquals(200, code)

    def test_pagination(self):
        handle = Handle('request', 'authentication')
        (data, code) = handle.success([1, 2, 3], number_results=3, page_length=10, page_number=1)
        self.assertEquals({
            'status': 'success',
            'error': '',
            'data': [1, 2, 3],
            'pagination': {'numberResults': 3, 'pageLength': 10, 'pageNumber': 1},
            'inputErrors': {},
        }, data)
        self.assertEquals(200, code)

    def test_error(self):
        handle = Handle('request', 'authentication')
        (data, code) = handle.error('bah', 400)
        self.assertEquals({
            'status': 'clientError',
            'error': 'bah',
            'data': [],
            'pagination': {},
            'inputErrors': {},
        }, data)
        self.assertEquals(400, code)

    def test_input_errors(self):
        handle = Handle('request', 'authentication')
        (data, code) = handle.input_errors({'age': 'required', 'date': 'tomorrow'})
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
        handle = Handle('request', authentication)
        handle.configure({})
        (data, code) = handle()
        self.assertEquals({
            'status': 'success',
            'error': '',
            'data': [1, 2, 3],
            'pagination': {},
            'inputErrors': {},
        }, data)
        self.assertEquals(200, code)
        authentication.authenticate.assert_called_with('request')
