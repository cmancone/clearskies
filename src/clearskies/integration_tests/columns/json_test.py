import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context


class JsonTest(unittest.TestCase):
    def test_default(self):
        class MyModel(clearskies.Model):
            backend = clearskies.backends.MemoryBackend()
            id_column_name = "id"

            id = clearskies.columns.Uuid()
            my_data = clearskies.columns.Json()

        context = clearskies.contexts.Context(
            clearskies.endpoints.Create(
                MyModel,
                writeable_column_names=["my_data"],
                readable_column_names=["id", "my_data"],
            ),
            classes=[MyModel]
        )

        (status_code, response_data, response_headers) = context(request_method="POST", body={"my_data":{"count":[1,2,3,4,{"thing":True}]}})
        assert response_data["data"]["my_data"] == {"count":[1,2,3,4,{"thing":True}]}
