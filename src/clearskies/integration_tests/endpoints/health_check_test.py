import datetime
import unittest

import clearskies
from clearskies.contexts import Context


class HealthCheckTest(unittest.TestCase):
    def test_success(self):
        context = clearskies.contexts.Context(
            clearskies.endpoints.HealthCheck(),
        )
        (status_code, response_data, response_headers) = context()

        assert status_code == 200
        assert response_data["status"] == "success"

    def test_failure(self):
        context = clearskies.contexts.Context(
            clearskies.endpoints.HealthCheck(dependency_injection_names=["cursor"]),
        )
        (status_code, response_data, response_headers) = context()

        assert status_code == 500
        assert response_data["status"] == "failure"

    def test_classes(self):
        class MyClass:
            def __init__(self, cursor):
                pass

        context = clearskies.contexts.Context(
            clearskies.endpoints.HealthCheck(classes_to_build=[MyClass]),
        )
        (status_code, response_data, response_headers) = context()

        assert status_code == 500
        assert response_data["status"] == "failure"

    def test_callables(self):
        def my_function(cursor):
            pass

        context = clearskies.contexts.Context(
            clearskies.endpoints.HealthCheck(
                callables=[my_function],
            ),
        )
        (status_code, response_data, response_headers) = context()

        assert status_code == 500
        assert response_data["status"] == "failure"
