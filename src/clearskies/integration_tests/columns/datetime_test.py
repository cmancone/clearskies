import unittest
from unittest.mock import MagicMock, call
import datetime

import clearskies
from clearskies.contexts import Context

class DateTest(unittest.TestCase):
    def test_default(self):
        class MyModel(clearskies.Model):
            backend = clearskies.backends.MemoryBackend()
            id_column_name = "id"

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            my_datetime = clearskies.columns.Datetime()

        context = clearskies.contexts.Context(
            clearskies.endpoints.Create(
                MyModel,
                writeable_column_names=["name", "my_datetime"],
                readable_column_names=["id", "name", "my_datetime"],
            ),
            classes=[MyModel]
        )

        (status_code, response_data, response_headers) = context(request_method="POST", body={"name": "Bob", "my_datetime": "May 13th 2025 15:35:03UTC"})
        assert response_data["data"]["my_datetime"] == "2025-05-13T15:35:03+00:00"

        (status_code, response_data, response_headers) = context(request_method="POST", body={"name": "Bob", "my_datetime": "2025-05-13 15:35:03+00:00"})
        assert response_data["data"]["my_datetime"] == "2025-05-13T15:35:03+00:00"

        (status_code, response_data, response_headers) = context(request_method="POST", body={"name": "Bob", "my_datetime": "not a date"})
        assert "my_datetime" not in response_data["data"]
        assert "my_datetime" in response_data["input_errors"]
