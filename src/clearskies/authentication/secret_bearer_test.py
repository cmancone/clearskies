from .secret_bearer import SecretBearer
import unittest
from unittest.mock import MagicMock


class SecretBearerTest(unittest.TestCase):
    def test_headers(self):
        secret_bearer = SecretBearer('input_output', 'asdferqwerty')
        self.assertEquals({'Authorization': 'Bearer asdferqwerty'}, secret_bearer.headers())

    def test_good_auth(self):
        input_output = type('', (), {'get_request_header': MagicMock(return_value='Bearer asdferqwerty')})()
        secret_bearer = SecretBearer(input_output, 'asdferqwerty')
        self.assertTrue(secret_bearer.authenticate())
        input_output.get_request_header.assert_called_with('authorization', True)

    def test_bad_auth(self):
        input_output = type('', (), {'get_request_header': MagicMock(return_value='Bearer Asdferqwerty')})()
        secret_bearer = SecretBearer(input_output, 'asdferqwerty')
        self.assertFalse(secret_bearer.authenticate())
        input_output.get_request_header.assert_called_with('authorization', True)

    def test_bad_bearer_auth(self):
        input_output = type('', (), {'get_request_header': MagicMock(return_value='Bearer: asdferqwerty')})()
        secret_bearer = SecretBearer(input_output, 'asdferqwerty')
        self.assertFalse(secret_bearer.authenticate())
