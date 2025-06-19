import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context


class EmailTest(unittest.TestCase):
    def test_default(self):
        class MyModel(clearskies.Model):
            backend = clearskies.backends.MemoryBackend()
            id_column_name = "id"

            id = clearskies.columns.Uuid()
            email = clearskies.columns.Email()

        context = clearskies.contexts.Context(
            clearskies.endpoints.Create(
                MyModel,
                writeable_column_names=["email"],
                readable_column_names=["id", "email"],
            ),
            classes=[MyModel],
        )

        (status_code, response_data, response_headers) = context(
            request_method="POST", body={"email": "test@example.com"}
        )
        assert response_data["data"]["email"] == "test@example.com"

        (status_code, response_data, response_headers) = context(request_method="POST", body={"email": "Bob"})
        assert "email" not in response_data["data"]
        assert "email" in response_data["input_errors"]
