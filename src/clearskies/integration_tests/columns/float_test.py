import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context


class FloatTest(unittest.TestCase):
    def test_default(self):
        class MyModel(clearskies.Model):
            backend = clearskies.backends.MemoryBackend()
            id_column_name = "id"

            id = clearskies.columns.Uuid()
            score = clearskies.columns.Float()

        context = clearskies.contexts.Context(
            clearskies.endpoints.Create(
                MyModel,
                writeable_column_names=["score"],
                readable_column_names=["id", "score"],
            ),
            classes=[MyModel]
        )

        (status_code, response_data, response_headers) = context(request_method="POST", body={"score": 15.2})
        assert response_data["data"]["score"] == 15.2

        (status_code, response_data, response_headers) = context(request_method="POST", body={"score": "15.2"})
        assert "score" not in response_data["data"]
        assert "score" in response_data["input_errors"]
