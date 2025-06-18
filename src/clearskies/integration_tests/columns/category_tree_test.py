import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context


class CategoryTreeTest(unittest.TestCase):
    def test_default(self):
        class Tree(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend(silent_on_missing_tables=True)

            id = clearskies.columns.Uuid()
            parent_id = clearskies.columns.String()
            child_id = clearskies.columns.String()
            is_parent = clearskies.columns.Boolean()
            level = clearskies.columns.Integer()

        class Category(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend(silent_on_missing_tables=True)

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            parent_id = clearskies.columns.CategoryTree(Tree)
            parent = clearskies.columns.BelongsToModel("parent_id")
            children = clearskies.columns.CategoryTreeChildren("parent_id")
            descendants = clearskies.columns.CategoryTreeDescendants("parent_id")
            ancestors = clearskies.columns.CategoryTreeAncestors("parent_id")

        def test_category_tree(category: Category):
            root_1 = category.create({"name": "Root 1"})
            root_2 = category.create({"name": "Root 2"})
            sub_1_root_1 = category.create({"name": "Sub 1 of Root 1", "parent_id": root_1.id})
            sub_2_root_1 = category.create({"name": "Sub 2 of Root 1", "parent_id": root_1.id})
            sub_sub = category.create({"name": "Sub Sub", "parent_id": sub_1_root_1.id})
            sub_1_root_2 = category.create({"name": "Sub 1 of Root 2", "parent_id": root_2.id})

            return {
                "descendants_of_root_1": [descendant.name for descendant in root_1.descendants],
                "children_of_root_1": [child.name for child in root_1.children],
                "descendants_of_root_2": [descendant.name for descendant in root_2.descendants],
                "ancestors_of_sub_sub": [ancestor.name for ancestor in sub_sub.ancestors],
            }

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(test_category_tree),
            classes=[Category, Tree],
        )
        (status_code, response_data, response_headers) = context()
        assert response_data["data"] == {
            "descendants_of_root_1": ["Sub 1 of Root 1", "Sub 2 of Root 1", "Sub Sub"],
            "children_of_root_1": ["Sub 1 of Root 1", "Sub 2 of Root 1"],
            "descendants_of_root_2": ["Sub 1 of Root 2"],
            "ancestors_of_sub_sub": ["Root 1", "Sub 1 of Root 1"],
        }
