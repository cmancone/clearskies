import unittest
from unittest.mock import MagicMock
from .column import Column
from ..input_requirements import MinimumLength
from ..autodoc.schema import String as AutoDocString
import clearskies


class RealColumn(Column):
    def __init__(self, di):
        super().__init__(di)

    def check_input(self, model, data):
        if "name" in data and data["name"] == "me":
            return "You are not allowed"


class ColumnTest(unittest.TestCase):
    def setUp(self):
        self.column = RealColumn("di")
        self.minimum_length = MinimumLength()
        self.minimum_length.column_name = "name"
        self.minimum_length.configure(10)

    def test_input_errors_requirements(self):
        self.column.configure("name", {"input_requirements": [self.minimum_length]}, RealColumn)
        errors = self.column.input_errors("model", {"name": "a"})
        self.assertEquals({"name": "'name' must be at least 10 characters long."}, errors)
        errors = self.column.input_errors("model", {"name": "me"})
        self.assertEquals({"name": "You are not allowed"}, errors)
        errors = self.column.input_errors("model", {"name": "1234567890"})
        self.assertEquals({}, errors)
        errors = self.column.input_errors("model", {"age": "1234567890"})
        self.assertEquals({}, errors)

    def test_documentation(self):
        self.column.configure("my_name", {"input_requirements": [self.minimum_length]}, RealColumn)
        doc = self.column.documentation()

        self.assertEquals(AutoDocString, doc.__class__)
        self.assertEquals("my_name", doc.name)

        more_doc = self.column.documentation(name="hey", example="sup", value="okay")
        self.assertEquals(AutoDocString, more_doc.__class__)
        self.assertEquals("hey", more_doc.name)
        self.assertEquals("sup", more_doc.example)
        self.assertEquals("okay", more_doc.value)

    def test_default(self):
        self.column.configure("my_name", {"default": "asdf"}, RealColumn)

        model = MagicMock()
        model.exists = False
        data = self.column.pre_save({}, model)
        self.assertDictEqual({"my_name": "asdf"}, data)

        model = MagicMock()
        model.exists = True
        data = self.column.pre_save({}, model)
        self.assertDictEqual({}, data)

        model = MagicMock()
        model.exists = False
        data = self.column.pre_save({"my_name": ""}, model)
        self.assertDictEqual({"my_name": ""}, data)

    def test_setable_hardcoded(self):
        self.column.configure("my_name", {"setable": "asdf"}, RealColumn)

        model = MagicMock()
        data = self.column.pre_save({}, model)
        self.assertDictEqual({"my_name": "asdf"}, data)

    def test_setable_callable(self):
        di = clearskies.di.StandardDependencies()
        di.bind("some_key", "cool")
        self.column = RealColumn(di)
        self.column.configure("my_name", {"setable": lambda some_key: some_key}, RealColumn)

        model = MagicMock()
        data = self.column.pre_save({}, model)
        self.assertDictEqual({"my_name": "cool"}, data)

    def test_created_by_authorization_data(self):
        input_output = MagicMock()
        input_output.get_authorization_data = MagicMock(return_value={"user_id": 5})
        di = clearskies.di.StandardDependencies()
        di.bind("input_output", input_output)
        self.column = RealColumn(di)
        self.column.configure(
            "my_name", {"created_by_source_type": "authorization_data", "created_by_source_key": "user_id"}, RealColumn
        )

        model = MagicMock()
        model.exists = False
        data = self.column.pre_save({}, model)
        self.assertDictEqual({"my_name": 5}, data)

        model = MagicMock()
        model.exists = True
        data = self.column.pre_save({"hey": "sup"}, model)
        self.assertDictEqual({"hey": "sup"}, data)
