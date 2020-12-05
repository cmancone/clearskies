import unittest
from unittest.mock import MagicMock, call
from .secrets import Secrets


class SecretsTest(unittest.TestCase):
    def setUp(self):
        self.configuration = 'configuration'
        self.api = type('', (), {})
        self.akeyless = type('', (), {
            'Configuration': MagicMock(return_value=self.configuration),
            'ApiClient': MagicMock(),
            'V2Api': MagicMock(return_value=self.api)
        })

    def test_get(self):
        self.akeyless.Auth = MagicMock(return_value='Auth')
        self.akeyless.GetSecretValue = MagicMock(return_value='SecretValueBody')
        self.api.auth = MagicMock(return_value=type('', (), {'token': 'mytoken'}))
        self.api.get_secret_value = MagicMock(return_value={'/my/secret/path': 'my_secret'})

        secrets = Secrets(self.akeyless, 'access-id', 'cloud-id')
        my_secret = secrets.get('/my/secret/path')

        self.assertEquals('my_secret', my_secret)
        self.akeyless.Auth.assert_called_with(access_id='access-id', access_type='aws_iam', cloud_id='cloud-id')
        self.api.auth.assert_called_with('Auth')
        self.akeyless.GetSecretValue.assert_called_with(names=['/my/secret/path'], token='mytoken')
        self.api.get_secret_value.assert_called_with('SecretValueBody')
