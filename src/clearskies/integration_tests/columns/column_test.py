import unittest
from unittest.mock import MagicMock, call
import datetime

import dateparser
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
            date_of_birth = clearskies.columns.Date()
            age = clearskies.columns.Integer(
                setable=lambda data, model, now:
                    (now-dateparser.parse(model.latest("date_of_birth", data))).total_seconds()/(86400*365),
            )
            created = clearskies.columns.Created()

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                lambda pets: pets.create({"date_of_birth": "2020-05-03"}),
                model_class=Pet,
                readable_column_names=["id", "name", "date_of_birth", "age"]
            ),
            classes=[Pet],
            now=datetime.datetime(2025, 5, 3, 0, 0, 0),
        )
        (status_code, response, response_headers) = context()
        assert response["data"]["name"] == "Spot"
        assert response["data"]["age"] == 5
        assert response["data"]["date_of_birth"] == "2020-05-03"

    def test_is_temporary_calc(self):
        class Pet(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            date_of_birth = clearskies.columns.Date(is_temporary=True)
            age = clearskies.columns.Integer(
                setable=lambda data, model, now:
                    (now-dateparser.parse(model.latest("date_of_birth", data))).total_seconds()/(86400*365),
            )
            created = clearskies.columns.Created()

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                lambda pets: pets.create({"name": "Spot", "date_of_birth": "2020-05-03"}),
                model_class=Pet,
                readable_column_names=["id", "age", "date_of_birth"],
            ),
            classes=[Pet],
        )
        (status_code, response, response_headers) = context()
        assert response["data"]["age"] == 5
        assert response["data"]["date_of_birth"] == None
