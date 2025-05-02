import unittest
from .update import Update
from ..column_types import String, Integer
from ..input_requirements import Required, MaximumLength
from ..authentication import Public, SecretBearer
from ..di import StandardDependencies
from .. import Model
from collections import OrderedDict
from ..contexts import test as context
import logging


class User(Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def columns_configuration(self):
        return OrderedDict(
            [
                ("id", {"class": String}),  # otherwise we'll use a UUID for the id, so I can't predict it
                ("name", {"class": String, "input_requirements": [Required]}),
                ("email", {"class": String, "input_requirements": [Required, (MaximumLength, 15)]}),
                ("age", {"class": Integer}),
            ]
        )


def no_bob(input_data):
    if input_data.get("email") == "bob@asdf.com":
        return {"email": "Bob is not allowed."}
    return {}


class UpdateTest(unittest.TestCase):
    def setUp(self):
        self.update = context(
            {
                "handler_class": Update,
                "handler_config": {
                    "model_class": User,
                    "columns": ["id", "name", "email", "age"],
                    "authentication": Public(),
                },
            }
        )
        self.users = self.update.build(User)
        self.users.create({"id": "5", "name": "", "email": "", "age": 0})

        # since this is a separate build, it will have a separate backend, which
        # is why we fetch a seperate users model.
        self.update_less_columns = context(
            {
                "handler_class": Update,
                "handler_config": {
                    "model_class": User,
                    "columns": ["id", "name", "age"],
                    "authentication": Public(),
                },
            }
        )
        self.users_less_columns = self.update_less_columns.build(User)
        self.users_less_columns.create({"id": "5", "name": "", "email": "", "age": 0})

    def test_save_flow(self):
        response = self.update(body={"name": "Conor", "email": "c@example.com", "age": 10}, routing_data={"id": 5})
        response_data = response[0]["data"]
        self.assertEqual(200, response[1])
        self.assertEqual("5", response_data["id"])
        self.assertEqual(10, response_data["age"])
        self.assertEqual("Conor", response_data["name"])
        self.assertEqual("c@example.com", response_data["email"])

    def test_upsert(self):
        response = self.update(body={"name": "Conor", "email": "c@example.com", "age": 10}, routing_data={"id": 10})
        response_data = response[0]["data"]
        self.assertEqual(200, response[1])
        self.assertEqual("10", response_data["id"])
        self.assertEqual(10, response_data["age"])
        self.assertEqual("Conor", response_data["name"])
        self.assertEqual("c@example.com", response_data["email"])

    def test_casing(self):
        update = context(
            {
                "handler_class": Update,
                "handler_config": {
                    "model_class": User,
                    "columns": ["id", "name", "email", "age"],
                    "authentication": Public(),
                    "internal_casing": "snake_case",
                    "external_casing": "TitleCase",
                },
            }
        )
        users = update.build(User)
        users.create({"id": "5", "name": "", "email": "", "age": 0})

        response = update(body={"Name": "Conor", "Email": "c@example.com", "Age": 10}, routing_data={"id": "5"})
        response_data = response[0]["Data"]
        self.assertEqual(200, response[1])
        self.assertEqual("5", response_data["Id"])
        self.assertEqual(10, response_data["Age"])
        self.assertEqual("Conor", response_data["Name"])
        self.assertEqual("c@example.com", response_data["Email"])

    def test_input_checks(self):
        response = self.update(body={"email": "cmancone@example.com", "age": 10}, routing_data={"id": 5})
        self.assertEqual(200, response[1])
        self.assertEqual(
            {"name": "'name' is required.", "email": "'email' must be at most 15 characters long."},
            response[0]["input_errors"],
        )

    def test_columns(self):
        response = self.update_less_columns(body={"name": "Conor", "age": 10}, routing_data={"id": 5})
        response_data = response[0]["data"]
        self.assertEqual(200, response[1])
        self.assertEqual("5", response_data["id"])
        self.assertEqual(10, response_data["age"])
        self.assertTrue("email" not in response_data)

    def test_extra_columns(self):
        response = self.update_less_columns(
            body={"name": "Conor", "age": 10, "email": "hey", "yo": "sup"}, routing_data={"id": 5}
        )
        self.assertEqual(
            {
                "email": "Input column 'email' is not an allowed column",
                "yo": "Input column 'yo' is not an allowed column",
            },
            response[0]["input_errors"],
        )

    def test_readable_writeable(self):
        update = context(
            {
                "handler_class": Update,
                "handler_config": {
                    "model_class": User,
                    "writeable_columns": ["id", "name", "age"],
                    "readable_columns": ["id", "name", "age", "email"],
                    "authentication": Public(),
                },
            }
        )
        users = update.build(User)
        users.create({"id": "5", "name": "Bob", "email": "default@email.com", "age": 10})

        response = update(body={"name": "Conor", "age": 10}, routing_data={"id": 5})
        response_data = response[0]["data"]
        self.assertEqual(200, response[1])
        self.assertEqual("5", response_data["id"])
        self.assertEqual(10, response_data["age"])
        self.assertEqual("default@email.com", response_data["email"])

    def test_auth_failure(self):
        secret_bearer = SecretBearer("secrets", "environment", logging)
        secret_bearer.configure(secret="asdfer", header_prefix="Bearer ")
        update = context(
            {
                "handler_class": Update,
                "handler_config": {
                    "model_class": User,
                    "writeable_columns": ["name", "age"],
                    "readable_columns": ["id", "name", "age", "email"],
                    "authentication": secret_bearer,
                },
            }
        )

        response = update(
            body={"id": 5, "name": "Conor", "email": "c@example.com", "age": 10},
            headers={"Authorization": "Bearer qwerty"},
        )
        self.assertEqual(401, response[1])
        self.assertEqual("client_error", response[0]["status"])
        self.assertEqual("Not Authenticated", response[0]["error"])

    def test_auth_success(self):
        secret_bearer = SecretBearer("secrets", "environment", logging)
        secret_bearer.configure(secret="asdfer", header_prefix="Bearer ")
        update = context(
            {
                "handler_class": Update,
                "handler_config": {
                    "model_class": User,
                    "writeable_columns": ["name", "age"],
                    "readable_columns": ["id", "name", "age", "email"],
                    "authentication": secret_bearer,
                },
            }
        )
        users = update.build(User)
        users.create({"id": 5, "name": "Bob", "email": "default@email.com", "age": 10})

        response = update(
            body={"name": "Conor", "email": "c@example.com", "age": 10},
            headers={"Authorization": "Bearer asdfer"},
            routing_data={"id": "5"},
        )
        self.assertEqual(200, response[1])

    def test_require_matching_id(self):
        response = self.update(body={"name": "Conor", "email": "c@example.com", "age": 10}, routing_data={"id": 10})
        self.assertEqual(404, response[1])
        self.assertEqual("Not Found", response[0]["error"])

    def test_doc(self):
        update = Update(StandardDependencies())
        update.configure(
            {
                "model": self.users,
                "readable_columns": ["id", "name", "email", "age"],
                "writeable_columns": ["name", "email", "age"],
                "authentication": Public(),
                "include_id_in_path": True,
            }
        )

        documentation = update.documentation()[0]

        self.assertEqual(4, len(documentation.parameters))
        self.assertEqual(["name", "email", "age", "id"], [param.definition.name for param in documentation.parameters])
        self.assertEqual([True, True, False, True], [param.required for param in documentation.parameters])

        self.assertEqual(3, len(documentation.responses))
        self.assertEqual([200, 200, 404], [response.status for response in documentation.responses])
        success_response = documentation.responses[0]
        self.assertEqual(
            ["status", "data", "pagination", "error", "input_errors"],
            [schema.name for schema in success_response.schema.children],
        )
        data_response_properties = success_response.schema.children[1].children
        self.assertEqual(["id", "name", "email", "age"], [prop.name for prop in data_response_properties])
        self.assertEqual(["string", "string", "string", "integer"], [prop._type for prop in data_response_properties])

    def test_custom_input_errors(self):
        update = context(
            {
                "handler_class": Update,
                "handler_config": {
                    "model_class": User,
                    "columns": ["id", "name", "email", "age"],
                    "authentication": Public(),
                    "input_error_callable": no_bob,
                },
            }
        )
        users = update.build(User)
        users.create({"id": "5", "name": "", "email": "", "age": 0})

        response = update(body={"name": "Conor", "email": "bob@asdf.com", "age": 10}, routing_data={"id": 5})
        self.assertEqual(200, response[1])
        self.assertEqual({"email": "Bob is not allowed."}, response[0]["input_errors"])

        response = update(body={"name": "Conor", "email": "bob2@asdf.com", "age": 10}, routing_data={"id": 5})
        self.assertEqual(200, response[1])
        self.assertEqual({}, response[0]["input_errors"])
