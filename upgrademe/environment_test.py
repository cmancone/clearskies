import unittest
from unittest.mock import MagicMock, call
from .environment import Environment
import os


class EnvironmentTest(unittest.TestCase):
    def setUp(self):
        self.secrets = type('', (), {'get': MagicMock(return_value='my_secret')})
        self.environment = Environment(
           '%s/environment_test_file' % os.getcwd(),
           {'env_in_environment': 'yup', 'also': 'secret:///another/secret/path'},
           self.secrets
        )

    def test_get_from_env(self):
        self.assertEquals('yup', self.environment.get('env_in_environment'))
        #self.akeyless.Auth = MagicMock(return_value='Auth')
        #self.akeyless.GetSecretValue = MagicMock(return_value='SecretValueBody')
        #self.api.auth = MagicMock(return_value=type('', (), {'token': 'mytoken'}))
        #self.api.get_secret_value = MagicMock(return_value={'/my/secret/path': 'my_secret'})

        #secrets = Secrets(self.akeyless, 'access-id', 'cloud-id')
        #my_secret = secrets.get('/my/secret/path')

        #self.assertEquals('my_secret', my_secret)
        #self.akeyless.Auth.assert_called_with(access_id='access-id', access_type='aws_iam', cloud_id='cloud-id')
        #self.api.auth.assert_called_with('Auth')
        #self.akeyless.GetSecretValue.assert_called_with(names=['/my/secret/path'], token='mytoken')
        #self.api.get_secret_value.assert_called_with('SecretValueBody')
