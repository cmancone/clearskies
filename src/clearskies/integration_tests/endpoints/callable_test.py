import unittest
import datetime

import clearskies
from clearskies.contexts import Context

class CallableTest(unittest.TestCase):
    def test_overview(self):
        class User(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()
            id = clearskies.columns.Uuid()
            first_name = clearskies.columns.String()
            last_name = clearskies.columns.String()
            age = clearskies.columns.Integer()

        def my_users_callable(users: User):
            bob = users.create({"first_name": "Bob", "last_name": "Brown", "age": 10})
            jane = users.create({"first_name": "Jane", "last_name": "Brown", "age": 10})
            alice = users.create({"first_name": "Alice", "last_name": "Green", "age": 10})

            return jane

        context = Context(
            clearskies.endpoints.Callable(
                my_users_callable,
                model_class=User,
                readable_column_names=["id", "first_name", "last_name"],
            ),
            classes=[User],
        )

        (status_code, response, response_headers) = context()
        users = context.di.build("users")
        jane = users.find("first_name=Jane")
        assert status_code == 200
        assert response["data"] == {
            "id": jane.id,
            "first_name": "Jane",
            "last_name": "Brown",
        }

    def test_input_schema(self):
        class ExpectedInput(clearskies.Schema):
            first_name = clearskies.columns.String(validators=[clearskies.validators.Required()])
            last_name = clearskies.columns.String()
            age = clearskies.columns.Integer(validators=[clearskies.validators.MinimumValue(0)])

        context = Context(clearskies.endpoints.Callable(
            lambda request_data: request_data,
            request_methods=["POST"],
            input_schema=ExpectedInput,
        ))

        (status_code, response, response_headers) = context(body={"first_name":"Jane","last_name":"Doe","age":1}, request_method="POST")
        assert status_code == 200
        assert response["data"] == {"first_name": "Jane", "last_name": "Doe", "age": 1}

        (status_code, response, response_headers) = context(body={"last_name":10,"age":-1,"check":"cool"}, request_method="POST")
        assert status_code == 200
        assert response["input_errors"] == {
            "age": "'age' must be at least 0.",
            "first_name": "'first_name' is required.",
            "last_name": "value should be a string",
            "check": "Input column check is not an allowed input column."
        }

    def test_standard_response(self):
        context = Context(clearskies.endpoints.Callable(
            lambda: {"hello": "world"},
            return_standard_response=True,
        ))

        (status_code, response, response_headers) = context()
        assert response["data"] == {"hello": "world"}

        context = Context(clearskies.endpoints.Callable(
            lambda: {"hello": "world"},
            return_standard_response=False,
        ))

        (status_code, response, response_headers) = context()
        assert response == {"hello": "world"}
