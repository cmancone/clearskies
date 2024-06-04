import unittest
import logging
from .create import Create
from ..column_types import String, Integer
from ..input_requirements import Required, MaximumLength
from ..authentication import Public, SecretBearer
from ..model import Model
from ..contexts import test
from collections import OrderedDict


class User(Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def columns_configuration(self):
        return OrderedDict(
            [
                ("name", {"class": String, "input_requirements": [Required]}),
                ("email", {"class": String, "input_requirements": [Required, (MaximumLength, 15)]}),
                ("age", {"class": Integer}),
            ]
        )


class CreateTest(unittest.TestCase):
    def setUp(self):
        self.create = test(
            {
                "handler_class": Create,
                "handler_config": {
                    "model_class": User,
                    "readable_columns": ["id", "name", "email", "age"],
                    "writeable_columns": ["name", "email", "age"],
                    "authentication": Public(),
                },
            }
        )
        self.users = self.create.build(User)

        self.create_no_email = test(
            {
                "handler_class": Create,
                "handler_config": {
                    "model_class": User,
                    "readable_columns": ["id", "name", "age"],
                    "writeable_columns": ["name", "age"],
                    "authentication": Public(),
                },
            }
        )

        secret_bearer = SecretBearer("secrets", "environment", logging)
        secret_bearer.configure(secret="asdfer", header_prefix="Bearer ")
        self.create_secret_bearer = test(
            {
                "handler_class": Create,
                "handler_config": {
                    "model_class": User,
                    "columns": ["name", "age", "email"],
                    "authentication": secret_bearer,
                },
            }
        )

    def test_save_flow(self):
        response = self.create(body={"name": "Conor", "email": "c@example.com", "age": 10})
        response_data = response[0]["data"]
        self.assertEqual(200, response[1])
        self.assertEqual(36, len(response_data["id"]))
        self.assertEqual(10, response_data["age"])
        self.assertEqual("Conor", response_data["name"])
        self.assertEqual("c@example.com", response_data["email"])
        self.assertEqual(1, len(self.users))
        id = response_data["id"]
        self.assertTrue(self.users.find(f"id={id}").exists)

    def test_casing(self):
        create = test(
            {
                "handler_class": Create,
                "handler_config": {
                    "model_class": User,
                    "readable_columns": ["id", "name", "email", "age"],
                    "writeable_columns": ["name", "email", "age"],
                    "authentication": Public(),
                    "internal_casing": "snake_case",
                    "external_casing": "TitleCase",
                },
            }
        )
        users = create.build(User)

        response = create(body={"Name": "Conor", "Email": "c@example.com", "Age": 10})
        response_data = response[0]["Data"]
        self.assertEqual(200, response[1])
        self.assertEqual(36, len(response_data["Id"]))
        self.assertEqual(10, response_data["Age"])
        self.assertEqual("Conor", response_data["Name"])
        self.assertEqual("c@example.com", response_data["Email"])
        self.assertEqual(1, len(users))
        id = response_data["Id"]
        self.assertTrue(users.find(f"id={id}").exists)

    def test_input_checks(self):
        response = self.create(body={"email": "cmancone@example.com", "age": 10})
        self.assertEqual(200, response[1])
        self.assertEqual(
            {"name": "'name' is required.", "email": "'email' must be at most 15 characters long."},
            response[0]["input_errors"],
        )

    def test_columns(self):
        response = self.create_no_email(body={"name": "Conor", "age": 10})
        response_data = response[0]["data"]
        self.assertEqual(200, response[1])
        self.assertEqual(36, len(response_data["id"]))
        self.assertEqual(10, response_data["age"])
        self.assertTrue("email" not in response_data)

    def test_extra_columns(self):
        response = self.create_no_email(body={"name": "Conor", "age": 10, "email": "hey", "yo": "sup"})
        self.assertEqual(
            {
                "email": "Input column 'email' is not an allowed column",
                "yo": "Input column 'yo' is not an allowed column",
            },
            response[0]["input_errors"],
        )

    def test_readable_writeable(self):
        create = test(
            {
                "handler_class": Create,
                "handler_config": {
                    "model_class": User,
                    "readable_columns": ["id", "name", "age", "email"],
                    "writeable_columns": ["name", "age"],
                    "authentication": Public(),
                },
            }
        )

        response = create(body={"name": "Conor", "age": 10})
        response_data = response[0]["data"]
        self.assertEqual(200, response[1])
        self.assertEqual(36, len(response_data["id"]))
        self.assertEqual(10, response_data["age"])
        self.assertEqual(None, response_data["email"])

    def test_auth_failure(self):
        response = self.create_secret_bearer(
            body={"name": "Conor", "email": "c@example.com", "age": 10},
            headers={"Authorization": "Bearer qwerty"},
        )
        self.assertEqual(401, response[1])
        self.assertEqual("client_error", response[0]["status"])
        self.assertEqual("Not Authenticated", response[0]["error"])

    def test_auth_success(self):
        response = self.create_secret_bearer(
            body={"name": "Conor", "email": "c@example.com", "age": 10},
            headers={"Authorization": "Bearer asdfer"},
        )
        self.assertEqual(200, response[1])
