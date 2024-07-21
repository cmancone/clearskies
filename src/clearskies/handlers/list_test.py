import unittest
from .list import List
from ..column_types import String, Integer
from ..di import StandardDependencies
from ..authentication import Public, SecretBearer, Authorization
from ..model import Model
from ..contexts import test as context
from collections import OrderedDict


class User(Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def columns_configuration(self):
        return OrderedDict(
            [
                ("id", {"class": String}),
                ("name", {"class": String}),
                ("email", {"class": String}),
                ("age", {"class": Integer}),
            ]
        )


class FilterAuth(Authorization):
    def filter_models(self, models, authorization_data, input_output):
        email = authorization_data.get("email")
        return models.where(f"email={email}")


class ListTest(unittest.TestCase):
    def setUp(self):
        self.list = context(
            {
                "handler_class": List,
                "handler_config": {
                    "model_class": User,
                    "readable_columns": ["id", "name", "email", "age"],
                    "searchable_columns": ["name"],
                    "default_sort_column": "email",
                    "authentication": Public(),
                },
            }
        )
        self.users = self.list.build(User)
        self.users.create({"id": "1", "name": "ronoc", "email": "cmancone1@example.com", "age": "6"})
        self.users.create({"id": "2", "name": "conor", "email": "cmancone2@example.com", "age": "8"})
        self.users.create({"id": "5", "name": "conor", "email": "cmancone3@example.com", "age": "15"})
        self.users.create({"id": "8", "name": "ronoc", "email": "cmancone4@example.com", "age": "25"})
        self.users.create({"id": "12", "name": "ronoc", "email": "cmancone5@example.com", "age": "35"})

    def test_simple_list(self):
        response = self.list()
        json_response = response[0]
        response_data = json_response["data"]
        self.assertEqual(200, response[1])
        self.assertEqual("success", json_response["status"])
        self.assertEqual({"number_results": 5, "next_page": {}, "limit": 100}, json_response["pagination"])
        self.assertEqual({"id": "1", "name": "ronoc", "email": "cmancone1@example.com", "age": 6}, response_data[0])
        self.assertEqual({"id": "2", "name": "conor", "email": "cmancone2@example.com", "age": 8}, response_data[1])
        self.assertEqual({"id": "5", "name": "conor", "email": "cmancone3@example.com", "age": 15}, response_data[2])
        self.assertEqual({"id": "8", "name": "ronoc", "email": "cmancone4@example.com", "age": 25}, response_data[3])
        self.assertEqual({"id": "12", "name": "ronoc", "email": "cmancone5@example.com", "age": 35}, response_data[4])

    def test_user_input(self):
        response = self.list(query_parameters={"sort": "name", "direction": "desc"})
        json_response = response[0]
        response_data = json_response["data"]
        self.assertEqual(200, response[1])
        self.assertEqual("success", json_response["status"])
        self.assertEqual({"number_results": 5, "next_page": {}, "limit": 100}, json_response["pagination"])
        self.assertEqual({"id": "1", "name": "ronoc", "email": "cmancone1@example.com", "age": 6}, response_data[0])
        self.assertEqual({"id": "8", "name": "ronoc", "email": "cmancone4@example.com", "age": 25}, response_data[1])
        self.assertEqual({"id": "12", "name": "ronoc", "email": "cmancone5@example.com", "age": 35}, response_data[2])
        self.assertEqual({"id": "2", "name": "conor", "email": "cmancone2@example.com", "age": 8}, response_data[3])
        self.assertEqual({"id": "5", "name": "conor", "email": "cmancone3@example.com", "age": 15}, response_data[4])

    def test_configure(self):
        list = context(
            {
                "handler_class": List,
                "handler_config": {
                    "model_class": User,
                    "readable_columns": ["id", "name"],
                    "searchable_columns": ["name"],
                    "where": ["age>5", "age<10"],
                    "default_sort_column": "name",
                    "default_sort_direction": "desc",
                    "default_limit": 50,
                    "group_by": "id",
                    "authentication": Public(),
                    "internal_casing": "snake_case",
                    "external_casing": "TitleCase",
                },
            }
        )
        users = list.build(User)
        users.create({"id": "1", "name": "conor", "email": "cmancone1@example.com", "age": "6"})
        users.create({"id": "2", "name": "ronoc", "email": "cmancone1@example.com", "age": "8"})
        users.create({"id": "5", "name": "conor", "email": "cmancone1@example.com", "age": "15"})
        users.create({"id": "8", "name": "ronoc", "email": "cmancone2@example.com", "age": "25"})
        users.create({"id": "10", "name": "ronoc", "email": "cmancone2@example.com", "age": "30"})

        response = list()
        json_response = response[0]
        response_data = json_response["Data"]
        self.assertEqual(200, response[1])
        self.assertEqual("Success", json_response["Status"])
        self.assertEqual(2, len(response_data))
        self.assertEqual({"Id": "2", "Name": "ronoc"}, response_data[0])
        self.assertEqual({"Id": "1", "Name": "conor"}, response_data[1])
        self.assertEqual({"NumberResults": 2, "NextPage": {}, "Limit": 50}, json_response["Pagination"])

    def test_where_function(self):
        list = context(
            {
                "handler_class": List,
                "handler_config": {
                    "model_class": User,
                    "readable_columns": ["id", "name"],
                    "searchable_columns": ["name"],
                    "where": [lambda models: models.where("age>5").where("age<10")],
                    "default_sort_column": "name",
                    "default_sort_direction": "desc",
                    "default_limit": 50,
                    "group_by": "id",
                    "authentication": Public(),
                    "internal_casing": "snake_case",
                    "external_casing": "TitleCase",
                },
            }
        )
        users = list.build(User)
        users.create({"id": "1", "name": "conor", "email": "cmancone1@example.com", "age": "6"})
        users.create({"id": "2", "name": "ronoc", "email": "cmancone1@example.com", "age": "8"})
        users.create({"id": "5", "name": "conor", "email": "cmancone1@example.com", "age": "15"})
        users.create({"id": "8", "name": "ronoc", "email": "cmancone2@example.com", "age": "25"})
        users.create({"id": "10", "name": "ronoc", "email": "cmancone2@example.com", "age": "30"})

        response = list()
        json_response = response[0]
        response_data = json_response["Data"]
        self.assertEqual(200, response[1])
        self.assertEqual("Success", json_response["Status"])
        self.assertEqual(2, len(response_data))
        self.assertEqual({"Id": "2", "Name": "ronoc"}, response_data[0])
        self.assertEqual({"Id": "1", "Name": "conor"}, response_data[1])
        self.assertEqual({"NumberResults": 2, "NextPage": {}, "Limit": 50}, json_response["Pagination"])

    def test_output_map(self):
        list = context(
            {
                "handler_class": List,
                "handler_config": {
                    "model_class": User,
                    "readable_columns": ["id", "name", "email", "age"],
                    "searchable_columns": ["name"],
                    "default_sort_column": "email",
                    "authentication": Public(),
                    "output_map": lambda model: {"id": model.id, "awesome": model.name},
                },
            }
        )
        users = list.build(User)
        users.create({"id": "1", "name": "ronoc", "email": "cmancone1@example.com", "age": "6"})
        users.create({"id": "2", "name": "conor", "email": "cmancone2@example.com", "age": "8"})

        response = list()
        json_response = response[0]
        response_data = json_response["data"]
        self.assertEqual(200, response[1])
        self.assertEqual("success", json_response["status"])
        self.assertEqual({"number_results": 2, "next_page": {}, "limit": 100}, json_response["pagination"])
        self.assertEqual({"id": "1", "awesome": "ronoc"}, response_data[0])
        self.assertEqual({"id": "2", "awesome": "conor"}, response_data[1])

    def test_authorization(self):
        list = context(
            {
                "handler_class": List,
                "handler_config": {
                    "model_class": User,
                    "readable_columns": ["id", "name", "email", "age"],
                    "searchable_columns": ["name"],
                    "default_sort_column": "email",
                    "authentication": Public(),
                    "authorization": FilterAuth(),
                },
            }
        )
        users = list.build(User)
        users.create({"id": "1", "name": "ronoc", "email": "cmancone1@example.com", "age": "6"})
        users.create({"id": "2", "name": "conor", "email": "cmancone2@example.com", "age": "8"})

        response = list(authorization_data={"email": "cmancone2@example.com"})
        json_response = response[0]
        response_data = json_response["data"]
        self.assertEqual(200, response[1])
        self.assertEqual("success", json_response["status"])
        self.assertEqual({"number_results": 1, "next_page": {}, "limit": 100}, json_response["pagination"])
        self.assertEqual(
            {"id": "2", "name": "conor", "email": "cmancone2@example.com", "age": 8}, dict(response_data[0])
        )

    def test_doc(self):
        list = List(StandardDependencies())
        list.configure(
            {
                "model_class": User,
                "readable_columns": ["id", "name", "email", "age"],
                "searchable_columns": ["name", "email"],
                "default_sort_column": "email",
                "authentication": Public(),
            }
        )

        documentation = list.documentation()
        self.assertEqual(1, len(documentation))
        all_doc = documentation[0]

        self.assertEqual([""], [doc.relative_path for doc in documentation])
        self.assertEqual([["GET"]], [doc.request_methods for doc in documentation])

        # Check our 'all' endpoint which returns all records
        self.assertEqual(2, len(all_doc.responses))
        self.assertEqual([200, 400], [response.status for response in all_doc.responses])
        self.assertEqual(
            ["status", "data", "pagination", "error", "input_errors"],
            [schema.name for schema in all_doc.responses[0].schema.children],
        )
        data_response_properties = all_doc.responses[0].schema.children[1].item_definition.children
        self.assertEqual(["id", "name", "email", "age"], [prop.name for prop in data_response_properties])
        self.assertEqual(["string", "string", "string", "integer"], [prop._type for prop in data_response_properties])
        self.assertEqual(
            ["limit", "start", "sort", "direction"], [param.definition.name for param in all_doc.parameters]
        )
        self.assertEqual(
            ["url_parameter", "url_parameter", "url_parameter", "url_parameter"],
            [param.location for param in all_doc.parameters],
        )
