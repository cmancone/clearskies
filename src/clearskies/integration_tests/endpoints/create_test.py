import datetime
import unittest

import clearskies
from clearskies import columns, validators
from clearskies.contexts import Context


class CreateTest(unittest.TestCase):
    def test_overview(self):
        class MyAwesomeModel(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = columns.Uuid()
            name = clearskies.columns.String(
                validators=[
                    validators.Required(),
                    validators.MaximumLength(50),
                ]
            )
            email = columns.Email(validators=[validators.Unique()])
            some_number = columns.Integer()
            expires_at = columns.Date()
            created_at = columns.Created()

        utcnow = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)

        context = clearskies.contexts.Context(
            clearskies.endpoints.Create(
                MyAwesomeModel,
                readable_column_names=["id", "name", "email", "some_number", "expires_at", "created_at"],
                writeable_column_names=["name", "email", "some_number", "expires_at"],
            ),
            utcnow=utcnow,
        )
        (status_code, response_data, response_headers) = context(
            request_method="POST",
            body={"name": "Example", "email": "test@example.com", "some_number": 5, "expires_at": "2024-12-31"},
        )

        assert len(response_data["data"]["id"]) == 36
        assert response_data["data"]["name"] == "Example"
        assert response_data["data"]["email"] == "test@example.com"
        assert response_data["data"]["some_number"] == 5
        assert response_data["data"]["expires_at"] == "2024-12-31"
        assert response_data["data"]["created_at"] == utcnow.isoformat()
