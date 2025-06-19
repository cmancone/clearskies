import datetime
import unittest

import clearskies
from clearskies.contexts import Context


class AdvancedSearchTest(unittest.TestCase):
    def test_overview(self):
        class Company(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()

        class User(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            username = clearskies.columns.String()
            age = clearskies.columns.Integer()
            company_id = clearskies.columns.BelongsToId(Company, readable_parent_columns=["id", "name"])
            company = clearskies.columns.BelongsToModel("company_id")

        context = clearskies.contexts.Context(
            clearskies.endpoints.AdvancedSearch(
                model_class=User,
                readable_column_names=["id", "name", "username", "age", "company"],
                sortable_column_names=["name", "username", "age", "company.name"],
                searchable_column_names=["id", "name", "username", "age", "company_id", "company.name"],
                default_sort_column_name="name",
            ),
            bindings={
                "memory_backend_default_data": [
                    {
                        "model_class": Company,
                        "records": [
                            {"id": "5-5-5-5", "name": "Bob's Widgets"},
                            {"id": "3-3-3-3", "name": "New Venture"},
                            {"id": "7-7-7-7", "name": "Jane's Cool Stuff"},
                        ],
                    },
                    {
                        "model_class": User,
                        "records": [
                            {
                                "id": "1-2-3-4",
                                "name": "Bob Brown",
                                "username": "bobbrown",
                                "age": 18,
                                "company_id": "5-5-5-5",
                            },
                            {
                                "id": "1-2-3-5",
                                "name": "Jane Doe",
                                "username": "janedoe",
                                "age": 52,
                                "company_id": "7-7-7-7",
                            },
                            {"id": "1-2-3-6", "name": "Greg", "username": "greg", "age": 37, "company_id": "7-7-7-7"},
                            {
                                "id": "1-2-3-7",
                                "name": "Curious George",
                                "username": "curious",
                                "age": 7,
                                "company_id": "3-3-3-3",
                            },
                        ],
                    },
                ],
            },
        )

        (status_code, response_data, response_headers) = context()
        assert ["bobbrown", "curious", "greg", "janedoe"] == [record["username"] for record in response_data["data"]]

        (status_code, response_data, response_headers) = context(
            request_method="POST", body={"limit": 2, "start": 1, "sort": [{"column": "name", "direction": "desc"}]}
        )
        assert ["greg", "curious"] == [record["username"] for record in response_data["data"]]

        (status_code, response_data, response_headers) = context(
            request_method="POST",
            body={"sort": [{"column": "company.name", "direction": "desc"}, {"column": "age", "direction": "asc"}]},
        )
        assert ["curious", "greg", "janedoe", "bobbrown"] == [record["username"] for record in response_data["data"]]

        (status_code, response_data, response_headers) = context(
            request_method="POST",
            body={
                "where": [
                    {"column": "age", "operator": "<=", "value": 37},
                    {"column": "username", "operator": "in", "value": ["curious", "greg"]},
                ]
            },
        )
        assert ["curious", "greg"] == [record["username"] for record in response_data["data"]]
