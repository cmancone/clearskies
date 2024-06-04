import unittest
from collections import OrderedDict
from ..di import StandardDependencies
from .category_tree import CategoryTree as CategoryTreeColumn
from .string import String
from .integer import Integer
from ..model import Model


class CategoryTree(Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def columns_configuration(self):
        return OrderedDict(
            [
                ("parent_id", {"class": String}),
                ("child_id", {"class": String}),
                ("is_parent", {"class": Integer}),
                ("level", {"class": Integer}),
            ]
        )


class Category(Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def columns_configuration(self):
        return OrderedDict(
            [
                ("name", {"class": String}),
                ("parent_id", {"class": CategoryTreeColumn, "tree_models_class": CategoryTree}),
            ]
        )


class CategoryTreeTest(unittest.TestCase):
    def setUp(self):
        self.di = StandardDependencies(classes=[Category, CategoryTree])
        self.categories = self.di.build("category")
        self.category_tree = self.di.build("category_tree")

    def test_build_tree(self):
        root = self.categories.create({"name": "root"})
        sub = self.categories.create({"name": "sub", "parent_id": root.id})
        subsub = self.categories.create({"name": "subsub", "parent_id": sub.id})
        subsubsub = self.categories.create({"name": "subsubsub", "parent_id": subsub.id})
        subsubsubsub = self.categories.create({"name": "subsubsubsub", "parent_id": subsubsub.id})

        subsubsubtree = [
            tree.parent_id for tree in self.category_tree.where(f"child_id={subsubsubsub.id}").sort_by("level", "asc")
        ]
        self.assertEqual(
            [root.id, sub.id, subsub.id, subsubsub.id],
            subsubsubtree,
        )

        altsubsub = self.categories.create({"name": "altsubsub", "parent_id": sub.id})
        subsubsubsub.save({"parent_id": altsubsub.id})

        subsubsubtree = [
            tree.parent_id for tree in self.category_tree.where(f"child_id={subsubsubsub.id}").sort_by("level", "asc")
        ]
        self.assertEqual(
            [root.id, sub.id, altsubsub.id],
            subsubsubtree,
        )
