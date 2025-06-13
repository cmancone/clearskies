import unittest
from unittest.mock import MagicMock, call
from .environment import Environment
import os


class EnvironmentTest(unittest.TestCase):
    def setUp(self):
        self.secrets = type("", (), {"get": MagicMock(return_value="my_secret")})
        self.environment = Environment(
            "",
            {
                "env_in_environment": "yup",
                "also": "secret:///another/secret/path",
                "an_integer": 5,
            },
            self.secrets,
        )

    def test_get_from_env(self):
        self.assertEqual("yup", self.environment.get("env_in_environment"))

    def test_get_from_env_resolve_secret(self):
        self.assertEqual("my_secret", self.environment.get("also"))
        self.secrets.get.assert_called_with("/another/secret/path")

    def test_no_crash_for_ints(self):
        self.assertEqual(5, self.environment.get("an_integer"))
