import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context

class PhoneTest(unittest.TestCase):
    def test_default(self):
        class User(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            phone = clearskies.columns.Phone(usa_only=True)

        context = clearskies.contexts.Context(
            clearskies.endpoints.Create(
                User,
                writeable_column_names=["name", "phone"],
                readable_column_names=["id", "name", "phone"],
            ),
        )
        (status_code, response_data, response_headers) = context(
            request_method="POST",
            body={"name": "Bob", "phone": "+1 (555) 451-1234"}
        )
        assert response_data["data"]["phone"] == "15554511234"

        (status_code, response_data, response_headers) = context(
            request_method="POST",
            body={"name": "Bob", "phone": "555 451-1234"}
        )
        assert response_data["data"]["phone"] == "5554511234"

        (status_code, response_data, response_headers) = context(
            request_method="POST",
            body={"name": "Bob", "phone": "555 451-12341"}
        )
        assert "phone" not in response_data["data"]
        assert "phone" in response_data["input_errors"]
