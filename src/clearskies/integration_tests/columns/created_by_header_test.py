import datetime
import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context


class CreatedByHeaderTest(unittest.TestCase):
    def test_default(self):
        class MyModel(clearskies.Model):
            backend = clearskies.backends.MemoryBackend()
            id_column_name = "id"

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            custom_header = clearskies.columns.CreatedByHeader("my_custom_header")

        context = clearskies.contexts.Context(
            clearskies.endpoints.Create(
                MyModel,
                writeable_column_names=["name"],
                readable_column_names=["id", "name", "custom_header"],
            ),
            classes=[MyModel]
        )
        (status_code, response_data, response_headers) = context(
            request_method="POST",
            body={"name":"Bob"},
            request_headers={"my_custom_header": "some_value"}
        )
        assert response_data["data"]["custom_header"] == "some_value"
