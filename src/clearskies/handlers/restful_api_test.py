import unittest
from unittest.mock import MagicMock, call
from .restful_api import RestfulAPI
from ..column_types import String, Integer
from ..authentication import Public
from ..model import Model
from ..contexts import test as context
from ..column_types import String, Integer
from collections import OrderedDict
from ..di import StandardDependencies


class User(Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def columns_configuration(self):
        return OrderedDict(
            [
                ("name", {"class": String}),
                ("email", {"class": String}),
                ("age", {"class": Integer}),
            ]
        )


class RestfulAPITest(unittest.TestCase):
    def setUp(self):
        self.api = context(
            {
                "handler_class": RestfulAPI,
                "handler_config": {
                    "model_class": User,
                    "readable_columns": ["id", "name", "age", "email"],
                    "writeable_columns": ["name", "age", "email"],
                    "searchable_columns": ["name", "age"],
                    "sortable_columns": ["name"],
                    "default_sort_column": "name",
                    "where": ["age>5"],
                    "authentication": Public(),
                },
            }
        )
        self.users = self.api.build(User)
        self.users.create({"name": "conor", "email": "cmancone1@example.com", "age": "8"})
        self.users.create({"name": "conor", "email": "cmancone2@example.com", "age": "3"})
        self.users.create({"name": "conor", "email": "cmancone3@example.com", "age": "15"})
        self.users.create({"name": "ronoc", "email": "cmancone4@example.com", "age": "25"})
        self.users.create({"name": "ronoc", "email": "cmancone5@example.com", "age": "35"})
        self.first_user = self.users.find("age=8")

    def test_get_record(self):
        result = self.api(url=f"/{self.first_user.id}")
        self.assertEqual(200, result[1])
        self.assertEqual(
            {"id": self.first_user.id, "name": "conor", "email": "cmancone1@example.com", "age": 8},
            dict(result[0]["data"]),
        )
        self.assertEqual({}, result[0]["pagination"])

    def test_get_record_not_found(self):
        result = self.api(url="/343433433")
        self.assertEqual(404, result[1])

    def test_update_record(self):
        result = self.api(url=f"/{self.first_user.id}", method="PUT", body={"name": "jane"})
        self.assertEqual(200, result[1])
        self.assertEqual(
            {"id": self.first_user.id, "name": "jane", "email": "cmancone1@example.com", "age": 8},
            dict(result[0]["data"]),
        )
        self.assertEqual({}, result[0]["pagination"])

    def test_list(self):
        result = self.api()
        self.assertEqual(200, result[1])
        self.assertEqual(
            {"id": self.first_user.id, "name": "conor", "email": "cmancone1@example.com", "age": 8},
            dict(result[0]["data"][0]),
        )
        self.assertEqual({"limit": 100, "number_results": 4, "next_page": {}}, result[0]["pagination"])

    def test_create(self):
        result = self.api(method="POST", body={"name": "another", "email": "another@example.com", "age": 123})
        self.assertEqual(200, result[1])
        new_user = self.users.find("age=123")
        self.assertTrue(new_user.exists)
        self.assertEqual(
            {"id": new_user.id, "name": "another", "email": "another@example.com", "age": 123}, dict(result[0]["data"])
        )
        self.assertEqual({}, result[0]["pagination"])

    def test_get_record(self):
        result = self.api(url=f"/{self.first_user.id}", method="DELETE")
        self.assertEqual(200, result[1])
        self.assertEqual({}, dict(result[0]["data"]))
        self.assertEqual({}, result[0]["pagination"])
        self.assertEqual(0, len(self.users.where(f"id={self.first_user.id}")))

    def test_search(self):
        model = self.users.find("age=15")
        result = self.api(
            body={"where": [{"column": "age", "operator": "=", "value": 15}]}, url="/search", method="POST"
        )
        self.assertEqual(200, result[1])
        self.assertEqual(
            {"id": model.id, "name": "conor", "email": "cmancone3@example.com", "age": 15}, dict(result[0]["data"][0])
        )
        self.assertEqual({"limit": 100, "number_results": 1, "next_page": {}}, result[0]["pagination"])
