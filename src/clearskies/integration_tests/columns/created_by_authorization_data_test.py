import datetime
import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context


class CreatedByAuthorizationDataTest(unittest.TestCase):
    def test_default(self):
        class MyModel(clearskies.Model):
            backend = clearskies.backends.MemoryBackend()
            id_column_name = "id"

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            organization_id = clearskies.columns.CreatedByAuthorizationData("organization_id")

        class MyAuthentication(clearskies.authentication.Authentication):
            def authenticate(self, input_output) -> bool:
                input_output.authorization_data = {
                    "organization_id": "my-super-awesome-organization",
                }
                return True

        context = clearskies.contexts.Context(
            clearskies.endpoints.Create(
                MyModel,
                writeable_column_names=["name"],
                readable_column_names=["id", "name", "organization_id"],
                authentication=MyAuthentication(),
            ),
            classes=[MyModel],
        )
        (status_code, response_data, response_headers) = context(request_method="POST", body={"name": "Bob"})
        assert response_data["data"]["organization_id"] == "my-super-awesome-organization"
