from ..handlers.exceptions import ClientError
from .auth0_jwks import Auth0JWKS
import unittest
from unittest.mock import MagicMock
from types import SimpleNamespace


class Auth0JWKSTest(unittest.TestCase):
    def setUp(self):
        self.my_jwks = {
            'keys': [{'kid': 2}, {'kid': 3}, {'kid': 1}],
        }
        self.requests = SimpleNamespace(
            get=MagicMock(return_value=SimpleNamespace(json=lambda: self.my_jwks)),
        )
        self.jose_jwt = SimpleNamespace(
            get_unverified_header=lambda jwt: {'kid': 3},
            decode=MagicMock(),
        )

    def test_success(self):
        auth0_jwks = Auth0JWKS('environment', self.requests, self.jose_jwt)
        auth0_jwks.configure(auth0_domain='example.com', audience='sup')
        input_output = SimpleNamespace(
            get_request_header=MagicMock(return_value='Bearer asdfqwer')
        )
        self.assertTrue(auth0_jwks.authenticate(input_output))
        self.requests.get.assert_called_with('https://example.com/.well-known/jwks.json')
        input_output.get_request_header.assert_called_with('authorization', True)
        self.jose_jwt.decode.assert_called_with(
            'asdfqwer',
            {'kid': 3},
            algorithms=["RS256"],
            audience='sup',
            issuer='https://example.com/'
        )

    def test_key_mismatch(self):
        self.jose_jwt.get_unverified_header=lambda jwt: {'kid': 5}
        auth0_jwks = Auth0JWKS('environment', self.requests, self.jose_jwt)
        auth0_jwks.configure(auth0_domain='example.com', audience='sup')
        input_output = SimpleNamespace(
            get_request_header=MagicMock(return_value='Bearer asdfqwer')
        )
        with self.assertRaises(ClientError) as context:
            auth0_jwks.authenticate(input_output)
        self.assertEquals('No matching keys found', str(context.exception))

    def test_missing_bearer(self):
        self.jose_jwt.get_unverified_header=lambda jwt: {'kid': 5}
        auth0_jwks = Auth0JWKS('environment', self.requests, self.jose_jwt)
        auth0_jwks.configure(auth0_domain='example.com', audience='sup')
        input_output = SimpleNamespace(
            get_request_header=MagicMock(return_value='asdfqwer')
        )
        with self.assertRaises(ClientError) as context:
            auth0_jwks.authenticate(input_output)
        self.assertEquals("Missing 'Bearer ' prefix in authorization header", str(context.exception))
