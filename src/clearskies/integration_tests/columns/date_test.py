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
            my_date = clearskies.columns.Date()

        context = clearskies.contexts.Context(
            clearskies.endpoints.Create(
                MyModel,
                writeable_column_names=["name", "my_date"],
                readable_column_names=["id", "name", "my_date"],
            ),
            classes=[MyModel]
        )

        (status_code, response_data, response_headers) = context(request_method="POST", body={"name": "Bob", "my_date": "May 13th 2025"})
        assert response_data["data"]["my_date"] == "2025-05-13"

        (status_code, response_data, response_headers) = context(request_method="POST", body={"name": "Bob", "my_date": "2025-05-13"})
        assert response_data["data"]["my_date"] == "2025-05-13"

        (status_code, response_data, response_headers) = context(request_method="POST", body={"name": "Bob", "my_date": "not a date"})
        assert "my_date" not in response_data["data"]
        assert "my_date" in response_data["input_errors"]
