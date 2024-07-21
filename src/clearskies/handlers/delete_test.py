import unittest
import logging
from .delete import Delete
from ..column_types import String, Integer
from ..input_requirements import Required, MaximumLength
from ..authentication import Public, SecretBearer
from ..di import StandardDependencies
from ..model import Model
from ..contexts import test as context
from collections import OrderedDict


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


class DeleteTest(unittest.TestCase):
    def setUp(self):
        self.delete = context(
            {
                "handler_class": Delete,
                "handler_config": {
                    "model_class": User,
                    "authentication": Public(),
                },
            }
        )
        self.users = self.delete.build(User)
        self.users.create({"id": "5", "name": "", "email": "", "age": 0})

        self.secret_bearer = SecretBearer("secrets", "environment", logging)
        self.secret_bearer.configure(secret="asdfer", header_prefix="Bearer ")

    def test_delete_flow(self):
        response = self.delete(routing_data={"id": "5"})
        self.assertEqual("success", response[0]["status"])
        self.assertEqual(200, response[1])
        self.assertFalse(self.users.find("id=5").exists)

    def test_not_found(self):
        response = self.delete(routing_data={"id": "10"})
        self.assertEqual("client_error", response[0]["status"])
        self.assertEqual(404, response[1])
        self.assertTrue(self.users.find("id=5").exists)

    def test_auth_failure(self):
        delete = context(
            {
                "handler_class": Delete,
                "handler_config": {
                    "model_class": User,
                    "authentication": self.secret_bearer,
                },
            }
        )
        users = delete.build(User)
        users.create({"id": "5", "name": "Bob", "email": "default@email.com", "age": 10})

        response = delete(
            body={"id": 5},
            headers={"Authorization": "Bearer qwerty"},
        )
        self.assertEqual(401, response[1])
        self.assertEqual("client_error", response[0]["status"])
        self.assertEqual("Not Authenticated", response[0]["error"])
        self.assertTrue(users.find("id=5").exists)

    def test_auth_success(self):
        delete = context(
            {
                "handler_class": Delete,
                "handler_config": {
                    "model_class": User,
                    "authentication": self.secret_bearer,
                },
            }
        )
        users = delete.build(User)
        users.create({"id": "5", "name": "Bob", "email": "default@email.com", "age": 10})

        response = delete(
            routing_data={"id": 5},
            headers={"Authorization": "Bearer asdfer"},
        )
        self.assertEqual(200, response[1])
        self.assertFalse(users.find("id=5").exists)

    def test_documentation(self):
        delete = Delete(StandardDependencies())
        delete.configure(
            {
                "model_class": User,
                "authentication": Public(),
            }
        )

        documentation = delete.documentation()[0]

        self.assertEqual(1, len(documentation.parameters))
        self.assertEqual(2, len(documentation.responses))
        self.assertEqual([200, 404], [response.status for response in documentation.responses])
        success_response = documentation.responses[0]
        self.assertEqual(
            ["status", "data", "pagination", "error", "input_errors"],
            [schema.name for schema in success_response.schema.children],
        )
