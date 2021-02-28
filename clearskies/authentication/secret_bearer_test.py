from .secret_bearer import SecretBearer
import unittest
from unittest.mock import MagicMock


class SecretBearerTest(unittest.TestCase):
    def test_headers(self):
        secret_bearer = SecretBearer('asdferqwerty')
        self.assertEquals({'Authorization': 'Bearer asdferqwerty'}, secret_bearer.headers())

    def test_good_auth(self):
        headers = type('', (), {'get': MagicMock(return_value='Bearer asdferqwerty')})()
        request = type('', (), {'headers': headers})()
        secret_bearer = SecretBearer('asdferqwerty')
        self.assertTrue(secret_bearer.authenticate(request))
        request.headers.get.assert_called_with('authorization')

    def test_bad_auth(self):
        headers = type('', (), {'get': MagicMock(return_value='Bearer Asdferqwerty')})()
        request = type('', (), {'headers': headers})()
        secret_bearer = SecretBearer('asdferqwerty')
        self.assertFalse(secret_bearer.authenticate(request))
        request.headers.get.assert_called_with('authorization')

    def test_bad_bearer_auth(self):
        headers = type('', (), {'get': MagicMock(return_value='Bearer: asdferqwerty')})()
        request = type('', (), {'headers': headers})()
        secret_bearer = SecretBearer('asdferqwerty')
        self.assertFalse(secret_bearer.authenticate(request))
