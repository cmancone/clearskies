import datetime
import unittest

import clearskies
from clearskies.contexts import Context


class DeleteTest(unittest.TestCase):
    def test_overview(self):
        class User(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()
            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            username = clearskies.columns.String()

        context = clearskies.contexts.Context(
            clearskies.endpoints.Delete(
                model_class=User,
                url="/{id}",
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

        (status_code, response_data, response_headers) = context(url="/1-2-3-5", request_method="DELETE")
        assert response_data["status"] == "success"

        users = context.build(User)
        assert not users.find("id=1-2-3-5")
        assert bool(users.find("id=1-2-3-4"))
