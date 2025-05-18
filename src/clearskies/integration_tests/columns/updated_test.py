import unittest
from unittest.mock import MagicMock, call
import datetime

import clearskies
from clearskies.contexts import Context

class SelectTest(unittest.TestCase):
    def test_default(self):
        class MyModel(clearskies.Model):
            backend = clearskies.backends.MemoryBackend()
            id_column_name = "id"

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            created = clearskies.columns.Created()
            updated = clearskies.columns.Updated()

        def test_updated(my_models: MyModel) -> MyModel:
            my_model = my_models.create({"name": "Jane"})
            return my_model.updated.isoformat()

        now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(test_updated),
            classes=[MyModel],
            utcnow=now,
        )
        (status_code, response_data, response_headers) = context()
        assert response_data["data"] == now.isoformat()

