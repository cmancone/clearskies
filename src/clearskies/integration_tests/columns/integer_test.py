import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context


class IntegerTest(unittest.TestCase):
    def test_default(self):
        class MyModel(clearskies.Model):
            backend = clearskies.backends.MemoryBackend()
            id_column_name = "id"

            id = clearskies.columns.Uuid()
            age = clearskies.columns.Integer()

        context = clearskies.contexts.Context(
            clearskies.endpoints.Create(
                MyModel,
                writeable_column_names=["age"],
                readable_column_names=["id", "age"],
            ),
            classes=[MyModel]
        )

        (status_code, response_data, response_headers) = context(request_method="POST", body={"age": 20})
        assert response_data["data"]["age"] == 20

        (status_code, response_data, response_headers) = context(request_method="POST", body={"age": "asdf"})
        assert "age" not in response_data["data"]
        assert "age" in response_data["input_errors"]
