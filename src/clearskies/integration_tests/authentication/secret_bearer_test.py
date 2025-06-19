import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context


class SecretBearerTest(unittest.TestCase):
    def test_overview(self):
        def get_environment(key):
            if key == "MY_AUTH_SECRET":
                return "SUPERSECRET"
            raise KeyError("Oops")

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                lambda: {"hello": "world"},
                authentication=clearskies.authentication.SecretBearer(environment_key="MY_AUTH_SECRET"),
            ),
            bindings={
                "environment": SimpleNamespace(get=get_environment),
            },
        )
        (status_code, response_data, response_headers) = context(request_headers={"Authorization": "SUPERSECRET"})
        print(response_data)
        assert status_code == 200

        (status_code, response_data, response_headers) = context(request_headers={"Authorization": "supersecret"})
        assert status_code == 401

    def test_secret_key(self):
        def fetch_secret(path):
            if path == "/path/to/my/secret":
                return "SUPERSECRET"
            raise KeyError(f"Attempt to fetch non-existent secret: {path}")

        fake_secret_manager = SimpleNamespace(get=fetch_secret)

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                lambda: {"hello": "world"},
                authentication=clearskies.authentication.SecretBearer(secret_key="/path/to/my/secret"),
            ),
            bindings={
                "secrets": fake_secret_manager,
            },
        )
        (status_code, response_data, response_headers) = context(request_headers={"Authorization": "SUPERSECRET"})
        assert status_code == 200

        (status_code, response_data, response_headers) = context(request_headers={"Authorization": "supersecret"})
        assert status_code == 401

    def test_alternate_secret_key(self):
        def fetch_secret(path):
            if path == "/path/to/my/secret":
                return "SUPERSECRET"
            if path == "/path/to/alternate/secret":
                return "ALSOOKAY"
            raise KeyError(f"Attempt to fetch non-existent secret: {path}")

        fake_secret_manager = SimpleNamespace(get=fetch_secret)

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                lambda: {"hello": "world"},
                authentication=clearskies.authentication.SecretBearer(
                    secret_key="/path/to/my/secret",
                    alternate_secret_key="/path/to/alternate/secret",
                ),
            ),
            bindings={
                "secrets": fake_secret_manager,
            },
        )
        (status_code, response_data, response_headers) = context(request_headers={"Authorization": "SUPERSECRET"})
        assert status_code == 200

        (status_code, response_data, response_headers) = context(request_headers={"Authorization": "ALSOOKAY"})
        assert status_code == 200

        (status_code, response_data, response_headers) = context(request_headers={"Authorization": "supersecret"})
        assert status_code == 401

    def test_alternate_environment_key(self):
        def get_environment(key):
            if key == "MY_AUTH_SECRET":
                return "SUPERSECRET"
            if key == "MY_ALT_SECRET":
                return "ALSOOKAY"
            raise KeyError("Oops")

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                lambda: {"hello": "world"},
                authentication=clearskies.authentication.SecretBearer(
                    environment_key="MY_AUTH_SECRET",
                    alternate_environment_key="MY_ALT_SECRET",
                ),
            ),
            bindings={
                "environment": SimpleNamespace(get=get_environment),
            },
        )
        (status_code, response_data, response_headers) = context(request_headers={"Authorization": "SUPERSECRET"})
        assert status_code == 200

        (status_code, response_data, response_headers) = context(request_headers={"Authorization": "ALSOOKAY"})
        assert status_code == 200

        (status_code, response_data, response_headers) = context(request_headers={"Authorization": "supersecret"})
        assert status_code == 401

    def test_header_prefix(self):
        def get_environment(key):
            if key == "MY_AUTH_SECRET":
                return "SUPERSECRET"
            raise KeyError("Oops")

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                lambda: {"hello": "world"},
                authentication=clearskies.authentication.SecretBearer(
                    environment_key="MY_AUTH_SECRET", header_prefix="secret-token "
                ),
            ),
            bindings={
                "environment": SimpleNamespace(get=get_environment),
            },
        )
        (status_code, response_data, response_headers) = context(
            request_headers={"Authorization": "SECRET-TOKEN SUPERSECRET"}
        )
        assert status_code == 200

        (status_code, response_data, response_headers) = context(
            request_headers={"Authorization": "SECRET_TOKENSUPERSECRET"}
        )
        assert status_code == 401

        (status_code, response_data, response_headers) = context(request_headers={"Authorization": "SUPERSECRET"})
        assert status_code == 401
