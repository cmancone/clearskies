import datetime
import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context


class CreatedTest(unittest.TestCase):
    def test_default(self):
        class MyModel(clearskies.Model):
            backend = clearskies.backends.MemoryBackend()
            id_column_name = "id"
            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            created = clearskies.columns.Created()

        utcnow = datetime.datetime.now(datetime.timezone.utc)
        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                lambda my_models: my_models.create({"name": "An Example"}),
                model_class=MyModel,
                readable_column_names=["id", "name", "created"],
            ),
            classes=[MyModel],
            utcnow=utcnow,
        )
        (status_code, response_data, response_headers) = context()
        assert response_data["data"]["created"] == utcnow.isoformat(timespec="seconds")
