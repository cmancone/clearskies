import unittest
from .health_check import HealthCheck
from unittest.mock import MagicMock
from ..contexts import test
from ..di import StandardDependencies


class HealthCheckTest(unittest.TestCase):
    def test_simple_success(self):
        health_check = test({"handler_class": HealthCheck, "handler_config": {}})
        response = health_check()
        response_data = response[0]["data"]
        self.assertEqual("success", response[0]["status"])
        self.assertEqual(200, response[1])

    def test_callable_success(self):
        test_callable = MagicMock(return_value=True)
        health_check = test(
            {
                "handler_class": HealthCheck,
                "handler_config": {
                    "callable": test_callable,
                },
            }
        )
        response = health_check()
        response_data = response[0]["data"]
        self.assertEqual("success", response[0]["status"])
        self.assertEqual(200, response[1])
        test_callable.assert_called_once()

    def test_callable_failure(self):
        test_callable = MagicMock(return_value=False)
        health_check = test(
            {
                "handler_class": HealthCheck,
                "handler_config": {
                    "callable": test_callable,
                },
            }
        )
        response = health_check()
        response_data = response[0]["data"]
        self.assertEqual("failure", response[0]["status"])
        self.assertEqual(500, response[1])
        test_callable.assert_called_once()

    def test_check_dependencies_success(self):
        health_check = test(
            {
                "handler_class": HealthCheck,
                "handler_config": {
                    "services": ["sup"],
                },
            },
            bindings={"sup": "hey"},
        )
        response = health_check()
        response_data = response[0]["data"]
        self.assertEqual("success", response[0]["status"])
        self.assertEqual(200, response[1])

    def test_check_dependencies_failure(self):
        health_check = test(
            {
                "handler_class": HealthCheck,
                "handler_config": {
                    "services": ["sup"],
                },
            }
        )
        response = health_check()
        response_data = response[0]["data"]
        self.assertEqual("failure", response[0]["status"])
        self.assertEqual(500, response[1])

    def test_documentation(self):
        health_check = HealthCheck(StandardDependencies())
        health_check.configure({})

        documentation = health_check.documentation()[0]

        self.assertEqual(0, len(documentation.parameters))
        self.assertEqual(1, len(documentation.responses))
        self.assertEqual([200], [response.status for response in documentation.responses])
        success_response = documentation.responses[0]
        self.assertEqual(
            ["status", "data", "pagination", "error", "input_errors"],
            [schema.name for schema in success_response.schema.children],
        )
