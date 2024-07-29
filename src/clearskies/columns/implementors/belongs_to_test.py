import unittest
from unittest.mock import MagicMock, call
from collections import OrderedDict
from .belongs_to import BelongsTo
from .string import String
from .string import String
from .. import Model
from ..di import StandardDependencies


class MockModel(Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def columns_configuration(self):
        return OrderedDict(
            [
                ("id", {"class": String}),
                ("name", {"class": String}),
            ]
        )


class BelongsToTest(unittest.TestCase):
    def setUp(self):
        self.di = StandardDependencies(
            classes=[MockModel],
            bindings={"input_output": MagicMock()},
        )
        self.models = self.di.build("mock_model")
        self.belongs_to = BelongsTo(self.di)

    def test_require_proper_name(self):
        with self.assertRaises(ValueError) as context:
            self.belongs_to.configure("user", {"parent_models_class": MockModel}, BelongsToTest)
        self.assertIn(
            "Invalid name for column 'user' in 'BelongsToTest' - BelongsTo column names must end in '_id'",
            str(context.exception),
        )

        self.belongs_to.configure(
            "user", {"parent_models_class": MockModel, "model_column_name": "user_model"}, BelongsToTest
        )
        self.assertEqual("user_model", self.belongs_to.config("model_column_name"))

    def test_require_parent_models_class(self):
        with self.assertRaises(KeyError) as context:
            self.belongs_to.configure("user_id", {}, BelongsToTest)
        self.assertEqual(
            "\"Missing required configuration 'parent_models_class' for column 'user_id' in 'BelongsToTest'\"",
            str(context.exception),
        )

    def test_check_input_no_match(self):
        self.belongs_to.configure("user_id", {"parent_models_class": MockModel}, BelongsToTest)
        error = self.belongs_to.input_errors("model", {"user_id": "5"})
        self.assertEqual({"user_id": "Invalid selection for user_id: record does not exist"}, error)

    def test_check_input_match(self):
        self.models.create({"id": "10"})
        self.belongs_to.configure("user_id", {"parent_models_class": MockModel}, BelongsToTest)
        error = self.belongs_to.input_errors("model", {"user_id": "10"})
        self.assertEqual({}, error)

    def test_check_input_null(self):
        self.belongs_to.configure("user_id", {"parent_models_class": MockModel}, BelongsToTest)
        error = self.belongs_to.input_errors("model", {"user_id": None})
        self.assertEqual({}, error)

    def test_provide(self):
        self.models.create({"id": "2", "name": "hey"})
        self.belongs_to.configure("user_id", {"parent_models_class": MockModel}, BelongsToTest)
        self.assertTrue(self.belongs_to.can_provide("user"))
        self.assertFalse(self.belongs_to.can_provide("users"))

        user = self.belongs_to.provide({"user_id": "2"}, "user_id")
        self.assertEqual("2", user.id)
        self.assertEqual("hey", user.name)
