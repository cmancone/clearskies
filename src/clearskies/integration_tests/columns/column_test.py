import unittest
from unittest.mock import MagicMock, call
import datetime

import clearskies
from clearskies.contexts import Context

class ColumnTest(unittest.TestCase):
    def test_default(self):
        class Widget(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String(default="Jane Doe")

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                lambda widgets: widgets.create(no_data=True),
                model_class=Widget,
                readable_column_names=["id", "name"]
            ),
            classes=[Widget],
        )
        (status_code, response, response_headers) = context()
        assert response["data"]["name"] == "Jane Doe"

    def test_setable(self):
        class Pet(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String(setable="Spot")
            dob = clearskies.columns.Datetime(setable=lambda data, model, utcnow: utcnow - datetime.timedelta(days=365*model.latest("age", data)))
            age = clearskies.columns.Integer()
            created = clearskies.columns.Created()

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                lambda pets: pets.create({"age": 5}),
                model_class=Pet,
                readable_column_names=["id", "name", "dob", "age", "created"]
            ),
            classes=[Pet],
            utcnow=datetime.datetime(2025, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
        )
        (status_code, response, response_headers) = context()
        assert response["data"]["name"] == "Spot"
        assert response["data"]["age"] == 5
        assert response["data"]["dob"] == "2020-01-03T00:00:00+00:00"
