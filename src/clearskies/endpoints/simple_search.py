from __future__ import annotations

import inspect
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Callable

import clearskies.configs
import clearskies.exceptions
from clearskies import authentication, autodoc, typing
from clearskies.endpoints.list import List
from clearskies.functional import string
from clearskies.input_outputs import InputOutput

if TYPE_CHECKING:
    from clearskies import Column, Schema, SecurityHeader
    from clearskies.model import Model


class SimpleSearch(List):
    """
    Create an endpoint that supports searching by exact values via url/JSON parameters.

    This acts exactly like the list endpoint but additionally grants the client the ability to search records
    via URL parameters or JSON POST body parameters.  You just have to specify which columns are searchable.

    In the following example we tell the `SimpleSearch` endpoint that we want it to return records from the
    `Student` model, return `id`, `name`, and `grade` in the results, and allow the user to search by
    `name` and `grade`.  We also seed the memory backend with data so the endpoint has something to return:

    ```python
    import clearskies


    class Student(clearskies.Model):
        backend = clearskies.backends.MemoryBackend()
        id_column_name = "id"

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        grade = clearskies.columns.Integer()


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.SimpleSearch(
            Student,
            readable_column_names=["id", "name", "grade"],
            sortable_column_names=["name", "grade"],
            searchable_column_names=["name", "grade"],
            default_sort_column_name="name",
        ),
        bindings={
            "memory_backend_default_data": [
                {
                    "model_class": Student,
                    "records": [
                        {"id": "1-2-3-4", "name": "Bob", "grade": 5},
                        {"id": "1-2-3-5", "name": "Jane", "grade": 3},
                        {"id": "1-2-3-6", "name": "Greg", "grade": 3},
                        {"id": "1-2-3-7", "name": "Bob", "grade": 2},
                    ],
                },
            ],
        },
    )
    wsgi()
    ```

    Here is the basic operation of the endpoint itself, without any search parameters, in which case it behaves
    identically to the list endpoint:

    ```bash
    $ curl 'http://localhost:8080' | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "1-2-3-4",
                "name": "Bob",
                "grade": 5
            },
            {
                "id": "1-2-3-7",
                "name": "Bob",
                "grade": 2
            },
            {
                "id": "1-2-3-6",
                "name": "Greg",
                "grade": 3
            },
            {
                "id": "1-2-3-5",
                "name": "Jane",
                "grade": 3
            }
        ],
        "pagination": {},
        "input_errors": {}
    }
    ```

    We can then search on name via the `name` URL parameter:

    ```bash
    $ curl 'http://localhost:8080?name=Bob' | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "1-2-3-4",
                "name": "Bob",
                "grade": 5
            },
            {
                "id": "1-2-3-7",
                "name": "Bob",
                "grade": 2
            }
        ],
        "pagination": {},
        "input_errors": {}
    }
    ```

    and multiple search terms are allowed:

    ```bash
    $ curl 'http://localhost:8080?name=Bob&grade=2' | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "1-2-3-7",
                "name": "Bob",
                "grade": 2
            }
        ],
        "pagination": {},
    "input_errors": {}
    }
    ```

    Pagination and sorting work just like with the list endpoint:

    ```bash
    $ curl 'http://localhost:8080?sort=grade&direction=desc&limit=2' | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "1-2-3-4",
                "name": "Bob",
                "grade": 5
            },
            {
                "id": "1-2-3-5",
                "name": "Jane",
                "grade": 3
            }
        ],
        "pagination": {
            "number_results": 4,
            "limit": 2,
            "next_page": {
                "start": 2
            }
        },
        "input_errors": {}
    }

    $ curl 'http://localhost:8080?sort=grade&direction=desc&limit=2&start=2' | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "1-2-3-6",
                "name": "Greg",
                "grade": 3
            },
            {
                "id": "1-2-3-7",
                "name": "Bob",
                "grade": 2
            }
        ],
        "pagination": {},
        "input_errors": {}
    }
    ```
    """

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        model_class: type[Model],
        readable_column_names: list[str],
        sortable_column_names: list[str],
        searchable_column_names: list[str],
        default_sort_column_name: str,
        default_sort_direction: str = "ASC",
        default_limit: int = 50,
        maximum_limit: int = 200,
        where: typing.condition | list[typing.condition] = [],
        joins: typing.join | list[typing.join] = [],
        url: str = "",
        request_methods: list[str] = ["GET", "POST", "QUERY"],
        response_headers: list[str | Callable[..., list[str]]] = [],
        output_map: Callable[..., dict[str, Any]] | None = None,
        output_schema: Schema | None = None,
        column_overrides: dict[str, Column] = {},
        internal_casing: str = "snake_case",
        external_casing: str = "snake_case",
        security_headers: list[SecurityHeader] = [],
        description: str = "",
        authentication: authentication.Authentication = authentication.Public(),
        authorization: authentication.Authorization = authentication.Authorization(),
    ):
        self.request_methods = request_methods

        # we need to call the parent but don't have to pass along any of our kwargs.  They are all optional in our parent, and our parent class
        # just stores them in parameters, which we have already done.  However, the parent does do some extra initialization stuff that we need,
        # which is why we have to call the parent.
        super().__init__(model_class, readable_column_names, sortable_column_names, default_sort_column_name)

    def check_search_in_request_data(self, request_data: dict[str, Any], query_parameters: dict[str, Any]) -> None:
        for input_source_label, input_data in [("request body", request_data), ("URL data", query_parameters)]:
            for column_name, value in input_data.items():
                if column_name in self.allowed_request_keys and column_name not in self.searchable_column_names:
                    continue
                if column_name not in self.searchable_column_names:
                    raise clearskies.exceptions.ClientError(
                        f"Invalid request parameter found in {input_source_label}: '{column_name}'"
                    )
                [relationship_column_name, final_column_name] = self.unpack_column_name_with_relationship(column_name)
                column_to_check = relationship_column_name if relationship_column_name else final_column_name
                value_error = self.searchable_columns[column_to_check].check_search_value(
                    value, relationship_reference=final_column_name
                )
                if value_error:
                    raise clearskies.exceptions.InputErrors({column_name: value_error})

    def configure_model_from_request_data(
        self,
        model: Model,
        request_data: dict[str, Any],
        query_parameters: dict[str, Any],
        pagination_data: dict[str, Any],
    ) -> Model:
        model = super().configure_model_from_request_data(
            model,
            request_data,
            query_parameters,
            pagination_data,
        )

        for input_source in [request_data, query_parameters]:
            for column_name, value in input_source.items():
                if column_name not in self.searchable_column_names:
                    continue

                model = self.add_join(column_name, model)
                [relationship_column_name, column_name] = self.unpack_column_name_with_relationship(column_name)
                if relationship_column_name:
                    self.columns[relationship_column_name].add_search(model, value, relationship_reference=column_name)
                else:
                    model = self.columns[column_name].add_search(model, value, operator="=")

        return model

    def documentation_url_search_parameters(self) -> list[autodoc.request.Parameter]:
        docs = []
        for column in self._get_searchable_columns().values():
            column_doc = column.documentation()
            column_doc.name = self.auto_case_internal_column_name(column_doc.name)
            docs.append(
                autodoc.request.URLParameter(
                    column_doc,
                    description=f"Search by {column_doc.name} (via exact match)",
                )
            )
        return docs  # type: ignore
