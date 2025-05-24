import unittest
import datetime

import clearskies
from clearskies.contexts import Context

class ListTest(unittest.TestCase):
    def test_overview(self):
        class User(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()
            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            username = clearskies.columns.String()

        context = clearskies.contexts.Context(
            clearskies.endpoints.Get(
                model_class=User,
                url="/{id}",
                readable_column_names=["id", "name", "username"],
            ),
            classes=[User],
            bindings={
                "memory_backend_default_data": [
                    {
                        "model_class": User,
                        "records": [
                            {"id": "1-2-3-4", "name": "Bob Brown", "username": "bobbrown"},
                            {"id": "1-2-3-5", "name": "Jane Doe", "username": "janedoe"},
                            {"id": "1-2-3-6", "name": "Greg", "username": "greg"},
                        ],
                    },
                ]
            }
        )

        (status_code, response_data, response_headers) = context(url="/1-2-3-4")
        assert response_data["data"] == {
            "id": "1-2-3-4",
            "name": "Bob Brown",
            "username": "bobbrown"
        }

        (status_code, response_data, response_headers) = context(url="/1-2-3-5")
        assert response_data["data"] == {
            "id": "1-2-3-5",
            "name": "Jane Doe",
            "username": "janedoe"
        }

        (status_code, response_data, response_headers) = context(url="/notauser")
        assert status_code == 404
        assert response_data["error"] == "Not Found"

    def test_record_lookup_columm_name(self):
        class User(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()
            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            username = clearskies.columns.String()

        context = clearskies.contexts.Context(
            clearskies.endpoints.Get(
                model_class=User,
                url="/{username}",
                readable_column_names=["id", "name", "username"],
                record_lookup_column_name="username",
            ),
            bindings={
                "memory_backend_default_data": [
                    {
                        "model_class": User,
                        "records": [
                            {"id": "1-2-3-4", "name": "Bob Brown", "username": "bobbrown"},
                            {"id": "1-2-3-5", "name": "Jane Doe", "username": "janedoe"},
                            {"id": "1-2-3-6", "name": "Greg", "username": "greg"},
                        ],
                    },
                ],
            },
        )

        (status_code, response_data, response_headers) = context(url="/bobbrown")
        assert response_data["data"] == {
            "id": "1-2-3-4",
            "name": "Bob Brown",
            "username": "bobbrown"
        }

        (status_code, response_data, response_headers) = context(url="/janedoe")
        assert response_data["data"] == {
            "id": "1-2-3-5",
            "name": "Jane Doe",
            "username": "janedoe"
        }

        (status_code, response_data, response_headers) = context(url="/notauser")
        assert status_code == 404
        assert response_data["error"] == "Not Found"
