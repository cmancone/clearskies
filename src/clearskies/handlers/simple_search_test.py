import unittest
from .simple_search import SimpleSearch
from ..column_types import String, Integer
from ..di import StandardDependencies
from ..authentication import Public, SecretBearer
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


class SimpleSearchTest(unittest.TestCase):
    def setUp(self):
        self.simple_search = context(
            {
                "handler_class": SimpleSearch,
                "handler_config": {
                    "model_class": User,
                    "readable_columns": ["id", "name", "email", "age"],
                    "searchable_columns": ["id", "name", "email"],
                    "default_sort_column": "email",
                    "authentication": Public(),
                },
            }
        )
        self.users = self.simple_search.build(User)
        self.users.create({"id": "1", "name": "ronoc", "email": "cmancone1@example.com", "age": "6"})
        self.users.create({"id": "2", "name": "conor", "email": "cmancone2@example.com", "age": "8"})
        self.users.create({"id": "5", "name": "conor", "email": "cmancone3@example.com", "age": "15"})
        self.users.create({"id": "8", "name": "ronoc", "email": "cmancone4@example.com", "age": "25"})
        self.users.create({"id": "12", "name": "ronoc", "email": "cmancone5@example.com", "age": "35"})

        self.simple_search_with_wheres = context(
            {
                "handler_class": SimpleSearch,
                "handler_config": {
                    "model_class": User,
                    "readable_columns": ["id", "name", "email", "age"],
                    "searchable_columns": ["id", "name", "email"],
                    "where": ["age>5", "age<10"],
                    "default_sort_column": "name",
                    "default_sort_direction": "desc",
                    "group_by": "id",
                    "authentication": Public(),
                },
            }
        )
        self.users_with_wheres = self.simple_search_with_wheres.build(User)
        self.users_with_wheres.create({"id": "1", "name": "conor", "email": "cmancone1@example.com", "age": "6"})
        self.users_with_wheres.create({"id": "2", "name": "ronoc", "email": "cmancone1@example.com", "age": "8"})
        self.users_with_wheres.create({"id": "5", "name": "conor", "email": "cmancone1@example.com", "age": "15"})
        self.users_with_wheres.create({"id": "8", "name": "ronoc", "email": "cmancone2@example.com", "age": "25"})
        self.users_with_wheres.create({"id": "10", "name": "ronoc", "email": "cmancone2@example.com", "age": "30"})
        self.users_with_wheres.create({"id": "11", "name": "ronoc", "email": "cmancone3@example.com", "age": "7"})
        self.users_with_wheres.create({"id": "12", "name": "conor", "email": "cmancone4@example.com", "age": "9"})

    def test_simple_read(self):
        response = self.simple_search()
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

    def test_configure(self):
        response = self.simple_search_with_wheres()
        json_response = response[0]
        response_data = json_response["data"]
        self.assertEqual(200, response[1])
        self.assertEqual("success", json_response["status"])
        self.assertEqual(4, len(response_data))
        self.assertEqual({"id": "2", "name": "ronoc", "email": "cmancone1@example.com", "age": 8}, response_data[0])
        self.assertEqual({"id": "11", "name": "ronoc", "email": "cmancone3@example.com", "age": 7}, response_data[1])
        self.assertEqual({"id": "1", "name": "conor", "email": "cmancone1@example.com", "age": 6}, response_data[2])
        self.assertEqual({"id": "12", "name": "conor", "email": "cmancone4@example.com", "age": 9}, response_data[3])
        self.assertEqual({"number_results": 4, "next_page": {}, "limit": 100}, json_response["pagination"])

    def test_user_input(self):
        response = self.simple_search(
            query_parameters={
                "email": "cmancone3@example.com",
            }
        )
        json_response = response[0]
        response_data = json_response["data"]
        self.assertEqual(200, response[1])
        self.assertEqual("success", json_response["status"])
        self.assertEqual(1, len(response_data))
        self.assertEqual({"number_results": 1, "next_page": {}, "limit": 100}, json_response["pagination"])
        self.assertEqual({"id": "5", "name": "conor", "email": "cmancone3@example.com", "age": 15}, response_data[0])

    def test_case_map(self):
        simple_search = context(
            {
                "handler_class": SimpleSearch,
                "handler_config": {
                    "model_class": User,
                    "readable_columns": ["id", "name", "email", "age"],
                    "searchable_columns": ["name", "email"],
                    "default_sort_column": "email",
                    "authentication": Public(),
                    "internal_casing": "snake_case",
                    "external_casing": "TitleCase",
                },
            }
        )
        users = simple_search.build(User)
        users.create({"id": "1", "name": "ronoc", "email": "cmancone1@example.com", "age": "6"})
        users.create({"id": "5", "name": "conor", "email": "cmancone3@example.com", "age": "15"})
        users.create({"id": "12", "name": "ronoc", "email": "cmancone5@example.com", "age": "35"})

        response = simple_search(
            query_parameters={
                "Email": "cmancone3@example.com",
            }
        )
        json_response = response[0]
        response_data = json_response["Data"]
        self.assertEqual(200, response[1])
        self.assertEqual("Success", json_response["Status"])
        self.assertEqual(1, len(response_data))
        self.assertEqual({"NumberResults": 1, "NextPage": {}, "Limit": 100}, json_response["Pagination"])
        self.assertEqual({"Id": "5", "Name": "conor", "Email": "cmancone3@example.com", "Age": 15}, response_data[0])

    def test_user_input_with_config(self):
        response = self.simple_search_with_wheres(
            query_parameters={
                "sort": "name",
                "direction": "asc",
            },
            body={
                "email": "cmancone1@example.com",
            },
        )
        json_response = response[0]
        response_data = json_response["data"]
        self.assertEqual(200, response[1])
        self.assertEqual("success", json_response["status"])
        self.assertEqual(2, len(response_data))
        self.assertEqual({"number_results": 2, "next_page": {}, "limit": 100}, json_response["pagination"])
        self.assertEqual({"id": "1", "name": "conor", "email": "cmancone1@example.com", "age": 6}, response_data[0])
        self.assertEqual({"id": "2", "name": "ronoc", "email": "cmancone1@example.com", "age": 8}, response_data[1])

    def test_doc(self):
        simple_search = SimpleSearch(StandardDependencies())
        simple_search.configure(
            {
                "model_class": User,
                "readable_columns": ["id", "name", "email", "age"],
                "searchable_columns": ["name", "email"],
                "default_sort_column": "email",
                "authentication": Public(),
            }
        )

        documentation = simple_search.documentation()
        all_doc = documentation[0]
        self.assertEqual(2, len(documentation))

        self.assertEqual(["", ""], [doc.relative_path for doc in documentation])
        self.assertEqual([["GET"], ["POST"]], [doc.request_methods for doc in documentation])

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
            ["limit", "start", "sort", "direction", "name", "email"],
            [param.definition.name for param in all_doc.parameters],
        )
        self.assertEqual(
            [
                "url_parameter",
                "url_parameter",
                "url_parameter",
                "url_parameter",
                "url_parameter",
                "url_parameter",
            ],
            [param.location for param in all_doc.parameters],
        )
