from __future__ import annotations

import inspect
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Callable

import clearskies.configs
import clearskies.exceptions
from clearskies import authentication, autodoc, typing
from clearskies.endpoint import Endpoint
from clearskies.functional import string
from clearskies.input_outputs import InputOutput

if TYPE_CHECKING:
    from clearskies import Schema, SecurityHeader
    from clearskies.column import Column
    from clearskies.model import Model


class List(Endpoint):
    """
    Create a list endpoint that fetches and returns records to the end client.

    A list endpoint has four required parameters:

    | Name                       | Value                                                                                 |
    |----------------------------|---------------------------------------------------------------------------------------|
    | `model_class`              | The model class for the endpoint to use to find and return records.                   |
    | `readable_column_names`    | A list of columns from the model class that the endpoint should return to the client. |
    | `sortable_column_names`    | A list of columns that the client is allowed to sort by.                              |
    | `default_sort_column_name` | The default column to sort by.                                                        |

    Here's a basic working example:

    ```
    import clearskies


    class User(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()


    list_users = clearskies.endpoints.List(
        model_class=User,
        readable_column_names=["id", "name"],
        sortable_column_names=["id", "name"],
        default_sort_column_name="name",
    )

    wsgi = clearskies.contexts.WsgiRef(
        list_users,
        classes=[User],
        bindings={
            "memory_backend_default_data": [
                {
                    "model_class": User,
                    "records": [
                        {"id": "1-2-3-4", "name": "Bob"},
                        {"id": "1-2-3-5", "name": "Jane"},
                        {"id": "1-2-3-6", "name": "Greg"},
                    ],
                },
            ]
        },
    )
    wsgi()
    ```

    You can then fetch your records:

    ```
    $ curl 'http://localhost:8080/' | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {"id": "1-2-3-4", "name": "Bob"},
            {"id": "1-2-3-6", "name": "Greg"},
            {"id": "1-2-3-5", "name": "Jane"},
        ],
        "pagination": {
            "number_results": 3,
            "limit": 50,
            "next_page": {}
        },
        "input_errors": {}
    }
    ```

    Pagination can be set via query parameters or the JSON body:

    ```
    $ curl 'http://localhost:8080/?sort=name&direction=desc&limit=2' | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {"id": "1-2-3-5", "name": "Jane"},
            {"id": "1-2-3-6", "name": "Greg"},
        ],
        "pagination": {
            "number_results": 3,
            "limit": 2,
            "next_page": {"start": 2}
        },
        "input_errors": {}
    }
    ```

    In the response, '.pagination.next_page` is a dictionary that returns the query parameters to set in order to fetch the next page of results.
    Note that the pagination method depends on the backend.  The memory backend supports pagination via start/limit, while other backends may
    support alternate pagination schemes.  Clearskies automatically handles the difference, so it's important to use `.pagination.next_page` to fetch
    the next page of results.

    Use `where`, `joins`, and `group_by` to automatically adjust the query used by the list endpoint.  In particular, where is a list of either
    conditions (as a string) or a callable that can modify the query directly via the model class.  For example:

    ```
    list_users = clearskies.endpoints.List(
        model_class=User,
        readable_column_names=["id", "name"],
        sortable_column_names=["id", "name"],
        default_sort_column_name="name",
        where=[User.name.equals("Jane")],  # equivalent: where=["name=Jane"]
    )
    ```

    With the above definition, the list endpoint will only ever return records with a name of "Jane".  The following uses standard dependency
    injection rules to execute a similar filter based on arbitrary logic required:

    ```
    import datetime

    list_users = clearskies.endpoints.List(
        model_class=User,
        readable_column_names=["id", "name"],
        sortable_column_names=["id", "name"],
        default_sort_column_name="name",
        where=[lambda model, now: model.where("name=Jane") if now > datetime.datetime(2025, 1, 1) else model],
    )
    ```

    As shown in the above example, a function called in this way can request additional dependencies as needed, per the standard dependency rules.
    The function needs to return the adjusted model object, which is usually as simple as returning the result of `model.where(?)`.  While the
    above example uses a lambda function, of course you can attach any other kind of callable - a function, a method of a class, etc...
    """

    """
    The default column to sort by.
    """
    default_sort_column_name = clearskies.configs.ModelColumn("model_class")

    """
    The default sort direction (ASC or DESC).
    """
    default_sort_direction = clearskies.configs.Select(["ASC", "DESC"], default="ASC")

    """
    The number of records returned if the client doesn't specify a different number of records (default: 50).
    """
    default_limit = clearskies.configs.Integer(default=50)

    """
    The maximum number of records the client is allowed to request (0 == no limit)
    """
    maximum_limit = clearskies.configs.Integer(default=200)

    """
    A column to group by.
    """
    group_by_column_name = clearskies.configs.ModelColumn("model_class")

    readable_column_names = clearskies.configs.ReadableModelColumns("model_class")
    sortable_column_names = clearskies.configs.ReadableModelColumns("model_class", allow_relationship_references=True)
    searchable_column_names = clearskies.configs.SearchableModelColumns(
        "model_class", allow_relationship_references=True
    )

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        model_class: type[Model],
        readable_column_names: list[str],
        sortable_column_names: list[str],
        default_sort_column_name: str | None,
        default_sort_direction: str = "ASC",
        default_limit: int = 50,
        maximum_limit: int = 200,
        where: typing.condition | list[typing.condition] = [],
        joins: typing.join | list[typing.join] = [],
        url: str = "",
        request_methods: list[str] = ["GET"],
        response_headers: list[str | Callable[..., list[str]]] = [],
        output_map: Callable[..., dict[str, Any]] | None = None,
        output_schema: Schema | None = None,
        column_overrides: dict[str, Column] = {},
        group_by_column_name: str = "",
        internal_casing: str = "snake_case",
        external_casing: str = "snake_case",
        security_headers: list[SecurityHeader] = [],
        description: str = "",
        authentication: authentication.Authentication = authentication.Public(),
        authorization: authentication.Authorization = authentication.Authorization(),
    ):
        # we need to call the parent but don't have to pass along any of our kwargs.  They are all optional in our parent, and our parent class
        # just stores them in parameters, which we have already done.  However, the parent does do some extra initialization stuff that we need,
        # which is why we have to call the parent.
        super().__init__()

    @property
    def searchable_columns(self) -> dict[str, Column]:
        if self._searchable_columns is None:
            self._searchable_columns = {name: self.columns[name] for name in self.searchable_column_names}
        return self._searchable_columns

    @property
    def sortable_columns(self) -> dict[str, Column]:
        if self._sortable_columns is None:
            self._sortable_columns = {name: self.columns[name] for name in self.sortable_column_names}
        return self._sortable_columns

    @property
    def allowed_request_keys(self) -> list[str]:
        return [*["sort", "direction", "limit"], *self.searchable_column_names]

    @property
    def internal_request_keys(self) -> list[str]:
        return ["sort", "direction", "limit"]

    def handle(self, input_output: InputOutput):
        model = self.fetch_model_with_base_query(input_output)
        if not input_output.request_data and input_output.has_body():
            raise clearskies.exceptions.ClientError("Request body was not valid JSON")
        if input_output.request_data and not isinstance(input_output.request_data, dict):
            raise clearskies.exceptions.ClientError("When present, request body must be a JSON dictionary")
        request_data = self.map_input_to_internal_names(input_output.request_data)  # type: ignore
        query_parameters = self.map_input_to_internal_names(input_output.query_parameters)
        pagination_data = {}
        for key in model.allowed_pagination_keys():
            if key in request_data and key in query_parameters:
                original_name = self.auto_case_internal_column_name(key)
                raise clearskies.exceptions.ClientError(
                    f"Ambiguous request: key '{original_name}' is present in both the JSON body and URL data"
                )
            if key in request_data:
                pagination_data[key] = request_data[key]
                del request_data[key]
            if key in query_parameters:
                pagination_data[key] = query_parameters[key]
                del query_parameters[key]
        if request_data or query_parameters or pagination_data:
            self.check_request_data(request_data, query_parameters, pagination_data)
            model = self.configure_model_from_request_data(model, request_data, query_parameters, pagination_data)
        if not model.get_query().limit:
            model = model.limit(self.default_limit)
        if not model.get_query().sorts and self.default_sort_column_name:
            model = model.sort_by(
                self.default_sort_column_name,
                self.default_sort_direction,
                model.destination_name(),
            )
        if self.group_by_column_name:
            model = model.group_by(self.group_by_column_name)

        return self.success(
            input_output,
            [self.model_as_json(record, input_output) for record in model],
            number_results=len(model) if model.backend.can_count else None,
            limit=model.get_query().limit,
            next_page=model.next_page_data(),
        )

    def configure_model_from_request_data(
        self,
        model: Model,
        request_data: dict[str, Any],
        query_parameters: dict[str, Any],
        pagination_data: dict[str, Any],
    ) -> Model:
        limit = int(self.from_either(request_data, query_parameters, "limit", default=self.default_limit))
        model = model.limit(limit)
        if pagination_data:
            model = model.pagination(**pagination_data)
        sort = self.from_either(request_data, query_parameters, "sort")
        direction = self.from_either(request_data, query_parameters, "direction")
        if sort and direction:
            model = self.add_join(sort, model)
            [sort_column, sort_table] = self.resolve_references_for_query(sort)
            model = model.sort_by(sort_column, direction, sort_table)  # type: ignore

        return model

    def map_input_to_internal_names(self, data: dict[str, Any]) -> dict[str, Any]:
        if not data:
            return {}
        internal_request_keys = [*self.internal_request_keys, *self.model.allowed_pagination_keys()]
        for key in internal_request_keys:
            mapped_key = self.auto_case_internal_column_name(key)
            if mapped_key != key and mapped_key in data:
                data[key] = data[mapped_key]
                del data[mapped_key]
        # any non-internal fields are assumed to be column names and need to go
        # through the full mapping
        for key in set(self.allowed_request_keys) - set(internal_request_keys):
            mapped_key = self.auto_case_column_name(key, True)
            if mapped_key != key and mapped_key in data:
                data[key] = data[mapped_key]
                del data[mapped_key]

        # finally, if we have a sort key set then convert the value to the properly cased column name
        if "sort" in data:
            # we can't just take the sort value and convert it to internal casing because camel/title case
            # to snake_case can be ambiguous (while snake_case to camel/title is not)
            sort_column_map = {}
            for internal_name in self.sortable_column_names:
                external_name = self.auto_case_column_name(internal_name, True)
                sort_column_map[external_name] = internal_name
            # sometimes the sort may be a list of directives
            if isinstance(data["sort"], list):
                for index, sort_entry in enumerate(data["sort"]):
                    if "column" not in sort_entry:
                        continue
                    if sort_entry["column"] in sort_column_map:
                        sort_entry["column"] = sort_column_map[sort_entry["column"]]
            else:
                if data["sort"] in sort_column_map:
                    data["sort"] = sort_column_map[data["sort"]]

        return data

    def check_request_data(
        self, request_data: dict[str, Any], query_parameters: dict[str, Any], pagination_data: dict[str, Any]
    ) -> None:
        if pagination_data:
            error = self.model.validate_pagination_data(pagination_data, self.auto_case_internal_column_name)
            if error:
                raise clearskies.exceptions.ClientError(error)
        for key in request_data.keys():
            if key not in self.allowed_request_keys:
                raise clearskies.exceptions.ClientError(f"Invalid request parameter found in request body: '{key}'")
        for key in query_parameters.keys():
            if key not in self.allowed_request_keys:
                raise clearskies.exceptions.ClientError(f"Invalid request parameter found in URL data: '{key}'")
            if key in request_data:
                raise clearskies.exceptions.ClientError(
                    f"Ambiguous request: '{key}' was found in both the request body and URL data"
                )
        self.validate_limit(request_data, query_parameters)
        sort = self.from_either(request_data, query_parameters, "sort")
        direction = self.from_either(request_data, query_parameters, "direction")
        if sort and type(sort) != str:
            raise clearskies.exceptions.ClientError("Invalid request: 'sort' should be a string")
        if direction and type(direction) != str:
            raise clearskies.exceptions.ClientError("Invalid request: 'direction' should be a string")
        if sort or direction:
            if (sort and not direction) or (direction and not sort):
                raise clearskies.exceptions.ClientError(
                    "You must specify 'sort' and 'direction' together in the request - not just one of them"
                )
            if sort not in self.sortable_column_names:
                raise clearskies.exceptions.ClientError(f"Invalid request: invalid sort column")
            if direction.lower() not in ["asc", "desc"]:
                raise clearskies.exceptions.ClientError("Invalid request: direction must be 'asc' or 'desc'")
        self.check_search_in_request_data(request_data, query_parameters)

    def validate_limit(self, request_data: dict[str, Any], query_parameters: dict[str, Any]) -> None:
        limit = self.from_either(request_data, query_parameters, "limit")
        if limit is not None and type(limit) != int and type(limit) != float and type(limit) != str:
            raise clearskies.exceptions.ClientError("Invalid request: 'limit' should be an integer")
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                raise clearskies.exceptions.ClientError("Invalid request: 'limit' should be an integer")
        if limit:
            if limit > self.maximum_limit:
                raise clearskies.exceptions.ClientError(f"Invalid request: 'limit' must be at most {self.max_limit}")
            if limit < 0:
                raise clearskies.exceptions.ClientError(f"Invalid request: 'limit' must be positive")

    def check_search_in_request_data(self, request_data: dict[str, Any], query_parameters: dict[str, Any]):
        return None

    def unpack_column_name_with_relationship(self, column_name: str) -> list[str]:
        if "." not in column_name:
            return ["", column_name]
        return column_name.split(".", 1)

    def resolve_references_for_query(self, column_name: str) -> list[str | None]:
        """
        Takes the column name and returns the name and table.

        If it's just a column name, we assume the table is the table for our model class.
        If it's something like `belongs_to_column.column_name`, then it will find the appropriate
        table reference.
        """
        if not column_name:
            return [None, None]
        [relationship_column_name, column_name] = self.unpack_column_name_with_relationship(column_name)
        if not relationship_column_name:
            return [self.model.destination_name(), column_name]

        return [self.columns[relationship_column_name].join_table_alias(), column_name]

    def add_join(self, column_name: str, model: Model) -> Model:
        """
        Adds a join to the query for the given column name in the case where it references a column in a belongs to.

        If column_name is something like `belongs_to_column.column_name`, this will add have the belongs to column
        add it's typical join condition, so that further sorting/searching can work.

        If column_name is empty, or doesn't contain a period, then this does nothing.
        """
        if not column_name:
            return model
        [relationship_column_name, column_name] = self.unpack_column_name_with_relationship(column_name)
        if not relationship_column_name:
            return model
        return self.columns[relationship_column_name].add_join(model)

    def from_either(self, request_data, query_parameters, key, default=None, ignore_none=True):
        """
        Returns the key from either object.  Assumes it is not present in both
        """
        if key in request_data:
            if request_data[key] is not None or not ignore_none:
                return request_data[key]
        if key in query_parameters:
            if query_parameters[key] is not None or not ignore_none:
                return query_parameters[key]
        return default

    def documentation(self) -> list[autodoc.request.Request]:
        nice_model = string.camel_case_to_words(self.model_class.__name__)
        schema_model_name = string.camel_case_to_snake_case(self.model_class.__name__)
        data_schema = self.documentation_data_schema()

        authentication = self.authentication
        standard_error_responses = []
        if not getattr(authentication, "is_public", False):
            standard_error_responses.append(self.documentation_access_denied_response())
            if getattr(authentication, "can_authorize", False):
                standard_error_responses.append(self.documentation_unauthorized_response())

        return [
            autodoc.request.Request(
                f"Fetch the list of current {nice_model} records",
                [
                    self.documentation_success_response(
                        autodoc.schema.Array(
                            self.auto_case_internal_column_name("data"),
                            autodoc.schema.Object(nice_model, children=data_schema, model_name=schema_model_name),
                        ),
                        description=f"The matching {nice_model} records",
                        include_pagination=True,
                    ),
                    *standard_error_responses,
                    self.documentation_generic_error_response(),
                ],
                relative_path=self.url,
                request_methods=self.request_methods,
                parameters=self.documentation_request_parameters(),
                root_properties={
                    "security": self.documentation_request_security(),
                },
            ),
        ]

    def documentation_request_parameters(self) -> list[autodoc.request.Parameter]:
        return [
            *self.documentation_url_pagination_parameters(),
            *self.documentation_url_sort_parameters(),
            *self.documentation_url_search_parameters(),
            *self.documentation_json_search_parameters(),
        ]

    def documentation_models(self) -> dict[str, autodoc.schema.Schema]:
        schema_model_name = string.camel_case_to_snake_case(self.model_class.__name__)

        return {
            schema_model_name: autodoc.schema.Object(
                self.auto_case_internal_column_name("data"),
                children=self.documentation_data_schema(),
            ),
        }

    def documentation_url_pagination_parameters(self) -> list[autodoc.request.Parameter]:
        url_parameters = [
            autodoc.request.URLParameter(
                autodoc.schema.Integer(self.auto_case_internal_column_name("limit")),
                description="The number of records to return",
            ),
        ]

        for parameter in self.model.documentation_pagination_parameters(self.auto_case_internal_column_name):
            (schema, description) = parameter
            url_parameters.append(autodoc.request.URLParameter(schema, description=description))

        return url_parameters  # type: ignore

    def documentation_url_sort_parameters(self) -> list[autodoc.request.Parameter]:
        sort_columns = [self.auto_case_column_name(internal_name, True) for internal_name in self.sortable_column_names]
        directions = [self.auto_case_column_name(internal_name, True) for internal_name in ["asc", "desc"]]

        return [
            autodoc.request.URLParameter(
                autodoc.schema.Enum(
                    self.auto_case_internal_column_name("sort"),
                    sort_columns,
                    autodoc.schema.String(self.auto_case_internal_column_name("sort")),
                    example=self.auto_case_column_name("name", True),
                ),
                description=f"Column to sort by",
            ),
            autodoc.request.URLParameter(
                autodoc.schema.Enum(
                    self.auto_case_internal_column_name("direction"),
                    directions,
                    autodoc.schema.String(self.auto_case_internal_column_name("direction")),
                    example=self.auto_case_column_name("asc", True),
                ),
                description=f"Direction to sort",
            ),
        ]

    def documentation_json_pagination_parameters(self) -> list[autodoc.request.Parameter]:
        json_parameters = [
            autodoc.request.JSONBody(
                autodoc.schema.Integer(self.auto_case_internal_column_name("limit")),
                description="The number of records to return",
            ),
        ]

        for parameter in self.model.documentation_pagination_parameters(self.auto_case_internal_column_name):
            (schema, description) = parameter
            json_parameters.append(autodoc.request.JSONBody(schema, description=description))

        return json_parameters  # type: ignore

    def documentation_json_sort_parameters(self) -> list[autodoc.request.Parameter]:
        sort_columns = [self.auto_case_column_name(internal_name, True) for internal_name in self.sortable_column_names]
        directions = [self.auto_case_column_name(internal_name, True) for internal_name in ["asc", "desc"]]

        return [
            autodoc.request.JSONBody(
                autodoc.schema.Enum(
                    self.auto_case_internal_column_name("sort"),
                    sort_columns,
                    autodoc.schema.String(self.auto_case_internal_column_name("sort")),
                    example=self.auto_case_column_name("name", True),
                ),
                description=f"Column to sort by",
            ),
            autodoc.request.JSONBody(
                autodoc.schema.Enum(
                    self.auto_case_internal_column_name("direction"),
                    directions,
                    autodoc.schema.String(self.auto_case_internal_column_name("direction")),
                    example=self.auto_case_column_name("asc", True),
                ),
                description=f"Direction to sort",
            ),
        ]

    def documentation_url_search_parameters(self) -> list[autodoc.request.Parameter]:
        return []

    def documentation_json_search_parameters(self) -> list[autodoc.request.Parameter]:
        return []
