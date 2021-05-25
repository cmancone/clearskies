from .secret_bearer import SecretBearer
import unittest
from unittest.mock import MagicMock


class SecretBearerTest(unittest.TestCase):
    def test_headers_secret(self):
        secret_bearer = SecretBearer('environment')
        secret_bearer.configure(secret='asdferqwerty')
        self.assertEquals({'Authorization': 'Bearer asdferqwerty'}, secret_bearer.headers())

    def test_headers_environment_key(self):
        environment = type('', (), {'get': MagicMock(return_value='asdferqwerty')})()
        secret_bearer = SecretBearer(environment)
        secret_bearer.configure(environment_key='my_secret')
        self.assertEquals({'Authorization': 'Bearer asdferqwerty'}, secret_bearer.headers())
        environment.get.assert_called_with('my_secret')

    def test_good_auth(self):
        input_output = type('', (), {'get_request_header': MagicMock(return_value='Bearer asdferqwerty')})()
        secret_bearer = SecretBearer('environment')
        secret_bearer.configure(secret='asdferqwerty')
        self.assertTrue(secret_bearer.authenticate(input_output))
        input_output.get_request_header.assert_called_with('authorization', True)

    def test_bad_auth(self):
        input_output = type('', (), {'get_request_header': MagicMock(return_value='Bearer Asdferqwerty')})()
        secret_bearer = SecretBearer('environment')
        secret_bearer.configure(secret='asdferqwerty')
        self.assertFalse(secret_bearer.authenticate(input_output))
        input_output.get_request_header.assert_called_with('authorization', True)

    def test_bad_bearer_auth(self):
        input_output = type('', (), {'get_request_header': MagicMock(return_value='Bearer: asdferqwerty')})()
        secret_bearer = SecretBearer('environment')
        secret_bearer.configure(secret='asdferqwerty')
        self.assertFalse(secret_bearer.authenticate(input_output))

    def test_not_configured(self):
        secret_bearer = SecretBearer('environment')
        with self.assertRaises(ValueError) as context:
            secret_bearer.authenticate('input_output')
        self.assertEquals(
            "Attempted to use SecretBearer authentication class without providing the configuration",
            str(context.exception)
        )
