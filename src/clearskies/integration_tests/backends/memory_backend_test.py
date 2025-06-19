import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context


class MemoryBackendTest(unittest.TestCase):
    def test_swap(self):
        class UserPreference(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.CursorBackend()
            id = clearskies.columns.Uuid()

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                lambda user_preferences: user_preferences.create(no_data=True).id,
            ),
            classes=[UserPreference],
            class_overrides={
                clearskies.backends.CursorBackend: clearskies.backends.MemoryBackend(),
            },
        )
        (status_code, response, response_headers) = context()
        assert status_code == 200
        assert len(response["data"]) == 36

    def test_predefined_rows(self):
        class Owner(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            phone = clearskies.columns.Phone()

        class Pet(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            species = clearskies.columns.String()
            owner_id = clearskies.columns.BelongsToId(Owner, readable_parent_columns=["id", "name"])
            owner = clearskies.columns.BelongsToModel("owner_id")

        context = clearskies.contexts.Context(
            clearskies.endpoints.List(
                model_class=Pet,
                readable_column_names=["id", "name", "species", "owner"],
                sortable_column_names=["id", "name", "species"],
                default_sort_column_name="name",
            ),
            classes=[Owner, Pet],
            bindings={
                "memory_backend_default_data": [
                    {
                        "model_class": Owner,
                        "records": [
                            {"id": "1-2-3-4", "name": "John Doe", "phone": "555-123-4567"},
                            {"id": "5-6-7-8", "name": "Jane Doe", "phone": "555-321-0987"},
                        ],
                    },
                    {
                        "model_class": Pet,
                        "records": [
                            {"id": "a-b-c-d", "name": "Fido", "species": "Dog", "owner_id": "1-2-3-4"},
                            {"id": "e-f-g-h", "name": "Spot", "species": "Dog", "owner_id": "1-2-3-4"},
                            {"id": "i-j-k-l", "name": "Puss in Boots", "species": "Cat", "owner_id": "5-6-7-8"},
                        ],
                    },
                ],
            },
        )
        (status_code, response, response_headers) = context()
        assert response["data"] == [
            {"id": "a-b-c-d", "name": "Fido", "species": "Dog", "owner": {"id": "1-2-3-4", "name": "John Doe"}},
            {
                "id": "i-j-k-l",
                "name": "Puss in Boots",
                "species": "Cat",
                "owner": {"id": "5-6-7-8", "name": "Jane Doe"},
            },
            {"id": "e-f-g-h", "name": "Spot", "species": "Dog", "owner": {"id": "1-2-3-4", "name": "John Doe"}},
        ]
