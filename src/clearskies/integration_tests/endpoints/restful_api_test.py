import datetime
import unittest

import clearskies
from clearskies import columns
from clearskies.contexts import Context
from clearskies.validators import Required, Unique


class RestfulApiTest(unittest.TestCase):
    def test_overview(self):
        class User(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = columns.Uuid()
            name = columns.String(validators=[Required()])
            username = columns.String(
                validators=[
                    Required(),
                    Unique(),
                ]
            )
            age = columns.Integer(validators=[Required()])
            created_at = columns.Created()
            updated_at = columns.Updated()

        context = clearskies.contexts.Context(
            clearskies.endpoints.RestfulApi(
                url="users",
                model_class=User,
                readable_column_names=["id", "name", "username", "age", "created_at", "updated_at"],
                writeable_column_names=["name", "username", "age"],
                sortable_column_names=["id", "name", "username", "age", "created_at", "updated_at"],
                searchable_column_names=["id", "name", "username", "age", "created_at", "updated_at"],
                default_sort_column_name="name",
            )
        )

        (status_code, response_data, response_headers) = context(
            request_method="POST",
            body={"name": "Bob", "username": "bob", "age": 25},
            url="users",
        )
        bob_id = response_data["data"]["id"]
        assert response_data["data"]["name"] == "Bob"
        assert response_data["data"]["age"] == 25

        (status_code, response_data, response_headers) = context(
            request_method="POST",
            body={"name": "Alice", "username": "alice", "age": 22},
            url="users",
        )
        assert response_data["data"]["name"] == "Alice"
        assert response_data["data"]["age"] == 22
        alice_id = response_data["data"]["id"]

        (status_code, response_data, response_headers) = context(
            url=f"users/{bob_id}",
        )
        assert response_data["data"]["name"] == "Bob"
        assert response_data["data"]["age"] == 25

        (status_code, response_data, response_headers) = context(
            request_method="PATCH",
            body={"name": "Alice Smith", "age": 23},
            url=f"users/{alice_id}",
        )
        assert response_data["data"]["name"] == "Alice Smith"
        assert response_data["data"]["age"] == 23

        (status_code, response_data, response_headers) = context(
            request_method="DELETE",
            url=f"users/{bob_id}",
        )
        assert not response_data["data"]
        assert response_data["status"] == "success"

        (status_code, response_data, response_headers) = context(
            url="users",
        )
        assert response_data["status"] == "success"
        assert [record["name"] for record in response_data["data"]] == ["Alice Smith"]
