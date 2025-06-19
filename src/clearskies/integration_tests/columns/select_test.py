import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context


class SelectTest(unittest.TestCase):
    def test_default(self):
        class Order(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            total = clearskies.columns.Float()
            status = clearskies.columns.Select(["Open", "Processing", "Shipped", "Complete"])

        context = clearskies.contexts.Context(
            clearskies.endpoints.Create(
                Order,
                writeable_column_names=["total", "status"],
                readable_column_names=["id", "total", "status"],
            ),
        )

        (status_code, response_data, response_headers) = context(
            request_method="POST", body={"total": 125, "status": "Open"}
        )
        assert response_data["data"]["status"] == "Open"

        (status_code, response_data, response_headers) = context(
            request_method="POST", body={"total": 125, "status": "huh"}
        )
        assert "status" not in response_data["data"]
        assert "status" in response_data["input_errors"]
