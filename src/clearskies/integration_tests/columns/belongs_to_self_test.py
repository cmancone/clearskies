import unittest
from typing import Any
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context


class BelongsToSelfTest(unittest.TestCase):
    def test_basics(self):
        class Category(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            parent_id = clearskies.columns.BelongsToSelf()
            parent = clearskies.columns.BelongsToModel("parent_id")
            children = clearskies.columns.HasManySelf()

        def test_self_relationship(categories: Category) -> dict[str, Any]:
            root = categories.create({"name": "Root"})
            sub = categories.create({"name": "Sub", "parent": root})
            subsub_1 = categories.create({"name": "Sub Sub 1", "parent": sub})
            subsub_2 = categories.create({"name": "Sub Sub 2", "parent_id": sub.id})

            return {
                "root_from_child": subsub_1.parent.parent.name,
                "subsubs_from_sub": [subsub.name for subsub in sub.children]
            }

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(test_self_relationship),
            classes=[Category],
        )
        (status_code, response, response_headers) = context()
        assert response["data"] == {
            "root_from_child": "Root",
            "subsubs_from_sub": [
                "Sub Sub 1",
                "Sub Sub 2"
            ],
        }
