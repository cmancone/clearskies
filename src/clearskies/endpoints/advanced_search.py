from __future__ import annotations

import inspect
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Type

import clearskies.configs
import clearskies.exceptions
from clearskies import authentication, autodoc, typing
from clearskies.endpoints.simple_search import SimpleSearch
from clearskies.functional import string
from clearskies.input_outputs import InputOutput

if TYPE_CHECKING:
    from clearskies import SecurityHeader
    from clearskies.model import Model


class AdvancedSearch(SimpleSearch):
    """
    An endpoint that grants the client extensive control over searching and filtering.

    Rather than accepting URL parameters (like the SimpleSearch endpoint), this endpoint accepts a JSON POST
    body.  Search conditions are specified as a list of dictionaries containing `column`, `operator`, and
    `value`.  It also accepts up to two sort directives.  Of course, while this endpoint supports arbitrary
    searching, it won't work if the backend itself doesn't support it.  The following is the list of allowed
    keys in the JSON body:

    | Name  | Type                 | Description                                                                | Example |
    |-------|----------------------|----------------------------------------------------------------------------|---------|
    | sort  | list[dict[str, str]] | A list of sort directives containing `column` and `direction`              | `{"sort": [ {"column": "age", "direction": "desc} ] }` |
    | limit | int                  | The number of records to return                                            | `{"limit": `100`}` |
    | where | list[dict[str, Any]] | A list of conditions containing `column`, `operator`, and `value`          | `{"where": [ {"column": "age", "operator": ">", "value": 10} ] }` |
    | *     | str, int             | Pagination information.  The key name and value type depend on the backend | `{"start": 100}` |

    Here's an example making use of the AdvancedSearch endpoint:

    ```python
    import clearskies


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


    wsgi = clearskies.contexts.WsgiRef(
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
                        {
                            "id": "1-2-3-6",
                            "name": "Greg",
                            "username": "greg",
                            "age": 37,
                            "company_id": "7-7-7-7",
                        },
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
    wsgi()
    ```

    If you invoke the endpoint without any additional data, it will simply list all records:

    ```bash
    $ curl 'http://localhost:8080/' | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "1-2-3-4",
                "name": "Bob Brown",
                "username": "bobbrown",
                "age": 18,
                "company": {
                    "id": "5-5-5-5",
                    "name": "Bob's Widgets"
                }
            },
            {
                "id": "1-2-3-7",
                "name": "Curious George",
                "username": "curious",
                "age": 7,
                "company": {
                    "id": "3-3-3-3",
                    "name": "New Venture"
                }
            },
            {
                "id": "1-2-3-6",
                "name": "Greg",
                "username": "greg",
                "age": 37,
                "company": {
                    "id": "7-7-7-7",
                    "name": "Jane's Cool Stuff"
                }
            },
            {
                "id": "1-2-3-5",
                "name": "Jane Doe",
                "username": "janedoe",
                "age": 52,
                "company": {
                    "id": "7-7-7-7",
                    "name": "Jane's Cool Stuff"
                }
            }
        ],
        "pagination": {
            "number_results": 4,
            "limit": 50,
            "next_page": {}
        },
        "input_errors": {}
    }
    ```

    Of course you can also sort and paginate.  Keep in mind that pagination is backend-dependent:

    ```bash
    $ curl 'http://localhost:8080/' -d '{"sort":[ {"column": "name", "direction": "desc"} ], "limit": 2, "start": 1}' | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "1-2-3-6",
                "name": "Greg",
                "username": "greg",
                "age": 37,
                "company": {
                    "id": "7-7-7-7",
                    "name": "Jane's Cool Stuff"
                }
            },
            {
                "id": "1-2-3-7",
                "name": "Curious George",
                "username": "curious",
                "age": 7,
                "company": {
                    "id": "3-3-3-3",
                    "name": "New Venture"
                }
            }
        ],
        "pagination": {
            "number_results": 4,
            "limit": 2,
            "next_page": {
            "start": 3
            }
        },
        "input_errors": {}
    }

    ```

    Note that sorting on columns in related models is done via the syntax `relationship_column.column_name`.  These
    must be listed as such in the list of sortable/searchable columns, and then you use the same name to sort/search
    by them:

    ```bash
    $ curl 'http://localhost:8080/' -d '{"sort":[ {"column": "company.name", "direction": "desc"}, {"column": "age", "direction": "asc"} ]}' | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "1-2-3-7",
                "name": "Curious George",
                "username": "curious",
                "age": 7,
                "company": {
                    "id": "3-3-3-3",
                    "name": "New Venture"
                }
            },
                {
                "id": "1-2-3-6",
                "name": "Greg",
                "username": "greg",
                "age": 37,
                "company": {
                    "id": "7-7-7-7",
                    "name": "Jane's Cool Stuff"
                }
            },
                {
                "id": "1-2-3-5",
                "name": "Jane Doe",
                "username": "janedoe",
                "age": 52,
                "company": {
                    "id": "7-7-7-7",
                    "name": "Jane's Cool Stuff"
                }
            },
                {
                "id": "1-2-3-4",
                "name": "Bob Brown",
                "username": "bobbrown",
                "age": 18,
                "company": {
                    "id": "5-5-5-5",
                    "name": "Bob's Widgets"
                }
            }
        ],
        "pagination": {
            "number_results": 4,
            "limit": 50,
            "next_page": {}
        },
        "input_errors": {}
    }

    ```

    And finally searching:

    ```bash
    $ curl 'http://localhost:8080/' -d '{"where":[ {"column": "age", "operator": "<=", "value": 37}, {"column": "username", "operator": "in", "value": ["curious", "greg"]} ]}' | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "1-2-3-7",
                "name": "Curious George",
                "username": "curious",
                "age": 7,
                "company": {
                    "id": "3-3-3-3",
                    "name": "New Venture"
                }
            },
            {
                "id": "1-2-3-6",
                "name": "Greg",
                "username": "greg",
                "age": 37,
                "company": {
                    "id": "7-7-7-7",
                    "name": "Jane's Cool Stuff"
                }
            }
        ],
        "pagination": {
            "number_results": 2,
            "limit": 50,
            "next_page": {}
        },
        "input_errors": {}
    }

    ```

    In terms of the allowed search operators, the standard list of operators is:

     * `<=>`
     * `!=`
     * `<=`
     * `>=`
     * `>`
     * `<`
     * `=`
     * `in`
     * `is not null`
     * `is null`
     * `is not`
     * `is`
     * `like`

    Although not all operators are supported by all columns.  You can use `%` with the `LIKE` operator
    to perform a wildcard search.

    """

    @property
    def allowed_request_keys(self) -> list[str]:
        return self.internal_request_keys

    @property
    def internal_request_keys(self) -> list[str]:
        return ["sort", "limit", "where"]

    def check_request_data(
        self, request_data: dict[str, Any], query_parameters: dict[str, Any], pagination_data: dict[str, Any]
    ) -> None:
        if pagination_data:
            error = self.model.validate_pagination_data(pagination_data, self.auto_case_internal_column_name)
            if error:
                raise clearskies.exceptions.ClientError(error)
        if query_parameters:
            raise clearskies.exceptions.ClientError("Query parameters were found but are not supported.")
        for key in request_data.keys():
            if key not in self.allowed_request_keys:
                raise clearskies.exceptions.ClientError(
                    f"Invalid request parameter found in request body: '{key}'.  Expected parameters: "
                    + ", ".join([self.auto_case_internal_column_name(key) for key in self.allowed_request_keys])
                )
        self.validate_limit(request_data, {})
        sort_key_name = self.auto_case_internal_column_name("sort")
        sort = request_data.get(sort_key_name, [])
        if not isinstance(sort, list):
            raise clearskies.exceptions.ClientError(
                f"'{sort_key_name}' property in request body should be a list, but I found a value of type "
                + sort.__class__.__name
            )
        if sort:
            column_key_name = self.auto_case_internal_column_name("column")
            direction_key_name = self.auto_case_internal_column_name("direction")
            for index, sort_entry in enumerate(sort):
                if not isinstance(sort_entry, dict):
                    raise clearskies.exceptions.ClientError(
                        f"'{sort_key_name}' should be a list of dictionaries, but entry #{index + 1} is a value of type '{sort_entry.__class__.__name}', not a dict"
                    )
                for key_name in [column_key_name, direction_key_name]:
                    if not sort_entry.get(key_name):
                        raise clearskies.exceptions.ClientError(
                            f"Each entry in the sort list should contain both '{column_key_name}' and '{direction_key_name}' but entry #{index + 1} is missing '{key_name}'"
                        )
                    if not isinstance(sort_entry[key_name], str):
                        raise clearskies.exceptions.ClientError(
                            f"{key_name}' must be a string, but for entry #{index + 1} it is a value of type "
                            + sort_entry[key_name].__class__.__name__
                        )
                if sort_entry[direction_key_name].lower() not in ["asc", "desc"]:
                    raise clearskies.exceptions.ClientError(
                        f"{direction_key_name}' must be either 'ASC' or 'DESC', but a different value was found for entry #{index + 1}"
                    )
                if self.auto_case_column_name(sort_entry[column_key_name], False) not in self.sortable_column_names:
                    raise clearskies.exceptions.ClientError(
                        f"Invalid sort column for entry #{index + 1}.  Allowed values are: "
                        + ", ".join(
                            [
                                self.auto_case_column_name(column_name, False)
                                for column_name in self.sortable_column_names
                            ]
                        )
                    )
        where_key_name = self.auto_case_internal_column_name("where")
        where = request_data.get(where_key_name, [])
        if not isinstance(where, list):
            raise clearskies.exceptions.ClientError(
                f"'{where_key_name}' property in request body should be a list, but I found a value of type "
                + where.__class__.__name
            )
        if where:
            column_key_name = self.auto_case_internal_column_name("column")
            operator_key_name = self.auto_case_internal_column_name("operator")
            value_key_name = self.auto_case_internal_column_name("value")
            for index, where_entry in enumerate(where):
                if not isinstance(where_entry, dict):
                    raise clearskies.exceptions.ClientError(
                        f"'{where_key_name}' should be a list of dictionaries, but entry #{index + 1} is a value of type '{where_entry.__class__.__name}', not a dict"
                    )
                for key_name in [column_key_name, operator_key_name, value_key_name]:
                    if key_name not in where_entry:
                        raise clearskies.exceptions.ClientError(
                            f"Each entry in the where list should contain '{column_key_name}', '{operator_key_name}', and '{value_key_name}', but entry #{index + 1} is missing '{key_name}'"
                        )
                    if key_name != value_key_name and not isinstance(where_entry[key_name], str):
                        raise clearskies.exceptions.ClientError(
                            f"{key_name}' must be a string, but for entry #{index + 1} it is a value of type "
                            + sort_entry[key_name].__class__.__name__
                        )
                    if where_entry[column_key_name] not in self.searchable_column_names:
                        raise clearskies.exceptions.ClientError(
                            f"Invalid where column for entry #{index + 1}.  Allowed values are: "
                            + ", ".join(
                                [
                                    self.auto_case_column_name(column_name, True)
                                    for column_name in self.searchable_column_names
                                ]
                            )
                        )
                    [relationship_column_name, column_name] = self.unpack_column_name_with_relationship(
                        self.auto_case_column_name(where_entry[column_key_name], False),
                    )
                    operator = where_entry[operator_key_name].lower()
                    value = where_entry[value_key_name]
                    error_allowed_operators = None
                    if relationship_column_name:
                        column = self.columns[relationship_column_name]
                        if not column.is_allowed_search_operator(operator, relationship_reference=column_name):
                            error_allowed_operators = column.allowed_search_operators(
                                relationship_reference=column_name
                            )
                        else:
                            error = column.check_search_value(
                                value if operator != "in" else value[0],
                                where_entry[operator_key_name],
                                relationship_reference=column_name,
                            )
                    else:
                        column = self.columns[column_name]
                        if not column.is_allowed_search_operator(operator):
                            error_allowed_operators = column.allowed_search_operators()
                        else:
                            error = column.check_search_value(
                                value if operator != "in" else value[0], where_entry[operator_key_name]
                            )
                    if error_allowed_operators:
                        raise clearskies.exceptions.ClientError(
                            f"Invalid operator for entry #{index + 1}.  Allowed operators are: "
                            + ", ".join(column.allowed_search_operators(relationship_reference=column_name))
                        )
                    if error:
                        raise clearskies.exceptions.ClientError(f"Invalid search value for entry #{index + 1}: {error}")

    def configure_model_from_request_data(
        self,
        model: Model,
        request_data: dict[str, Any],
        query_parameters: dict[str, Any],
        pagination_data: dict[str, Any],
    ) -> Model:
        if pagination_data:
            model = model.pagination(**pagination_data)
        sort = request_data.get(self.auto_case_internal_column_name("sort"), [])
        if sort:
            column_key_name = self.auto_case_internal_column_name("column")
            direction_key_name = self.auto_case_internal_column_name("direction")
            model = self.add_join(sort[0][column_key_name], model)
            [primary_table_name, primary_column_name] = self.resolve_references_for_query(sort[0][column_key_name])
            primary_direction = sort[0][direction_key_name]

            if len(sort) > 1:
                [secondary_table_name, secondary_column_name] = self.resolve_references_for_query(
                    sort[1][column_key_name]
                )
                secondary_direction = sort[1][direction_key_name]
            else:
                secondary_column_name = ""
                secondary_direction = ""
                secondary_table_name = ""
            model = model.sort_by(
                primary_column_name if primary_column_name else "",
                primary_direction if primary_direction else "",
                primary_table_name=primary_table_name if primary_table_name else "",
                secondary_column_name=secondary_column_name if secondary_column_name else "",
                secondary_direction=secondary_direction if secondary_direction else "",
                secondary_table_name=secondary_table_name if secondary_table_name else "",
            )
        if request_data.get("limit"):
            model = model.limit(request_data["limit"])

        for where in request_data.get(self.auto_case_internal_column_name("where"), []):
            raw_column_name = self.auto_case_column_name(where[self.auto_case_internal_column_name("column")], False)
            [relationship_column_name, column_name] = self.unpack_column_name_with_relationship(raw_column_name)
            operator = where[self.auto_case_internal_column_name("operator")].lower()
            value = where[self.auto_case_internal_column_name("value")]

            model = self.add_join(raw_column_name, model)
            if relationship_column_name:
                model = self.columns[relationship_column_name].add_search(
                    model, value, operator=operator, relationship_reference=column_name
                )
            else:
                model = self.columns[column_name].add_search(model, value, operator=operator)

        return model

    def documentation_url_search_parameters(self) -> list[autodoc.request.Parameter]:
        return []
