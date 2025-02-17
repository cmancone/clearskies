from __future__ import annotations
import inspect
from typing import TYPE_CHECKING

from clearskies import autodoc
from clearskies import typing
from clearskies.endpoint import Endpoint
from collections import OrderedDict
from clearskies import autodoc
from clearskies.functional import string
from clearskies.input_outputs import InputOutput
import clearskies.configs
import clearskies.Exceptions

if TYPE_CHECKING:
    from clearskies.model import Model


class List(Endpoint):
    """
    Columns from the model class that should be returned to the client.
    """
    readable_column_names = clearskies.configs.ReadableModelColumns("model_class")

    """
    Columns from the model class that the client is allowed to sort by.
    """
    sortable_column_names = clearskies.configs.ReadableModelColumns("model_class", allow_relationship_references=True)

    """
    Columns from the model class that the client is allowed to search by
    """
    searchable_column_names = clearskies.configs.SearchableModelColumns("model_class", allow_relationship_references=True)

    """
    The default column to sort by.
    """
    default_sort_column_name = clearskies.configs.ModelColumn("model_class")

    """
    The default sort direction (ASC or DESC).
    """
    default_sort_direction = clearskies.configs.Select(["ASC", "DESC"], default="ASC")

    """
    The default pagination limit
    """
    default_limit = clearskies.configs.Integer(default=50)

    """
    The maximum limit the client is allowed to request (0 == no limit)
    """
    maximum_limit = clearskies.configs.Integer(default=200)

    """
    Additional conditions to always added to the results.
    """
    where = clearskies.configs.Conditions()

    """
    Additional joins to always add to the results.
    """
    joins = clearskies.configs.Joins()

    """
    A column to group by.
    """
    group_by = clearskies.configs.ModelColumn("model_class")

    allowed_request_keys = ["sort", "direction", "limit"]
    internal_request_keys = ["sort", "direction", "limit"]
    _searchable_columns = None
    _sortable_columns = None

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        readable_column_names: list[str],
        sortable_column_names: list[str],
        default_sort_column: str,
        default_sort_direction: str = "ASC",
        default_limit: int = 50,
        maximum_limit: int = 200,
        where: typing.condition | list[typing.condition] = [],
        joins: typing.join | list[typing.join] = [],
        url: str = "",
        request_methods: list[str] = ["GET"],
        response_headers: list[str | Callable[..., list[str]]] = [],
        output_map: Callable[..., dict[str, Any]] | None = None,
        column_overrides: dict[str, Column] = {},
        internal_casing: str = "snake_case",
        external_casing: str = "snake_case",
        security_headers: list[SecurityHeader] = [],
        description: str = "",
        authentication: Authentication = Public(),
        authorization: Authorization = Authorization(),
    ):
        # we need to call the parent but don't have to pass along any of our kwargs.  They are all optional in our parent, and our parent class
        # just stores them in parameters, which we have already done.  However, the parent does do some extra initialization stuff that we need,
        # which is why we have to call the parent.
        super().__init__()

    @property
    def searchable_columns(self) -> dict[str, Column]:
        if self._searchable_columns is None:
            self._searchable_columns = {name: self._columns[name] for name in self.searchable_column_names}
        return self._searchable_columns

    @property
    def sortable_columns(self) -> dict[str, Column]:
        if self._sortable_columns is None:
            self._sortable_columns = {name: self._columns[name] for name in self.sortable_column_names}
        return self._sortable_columns

    def handle(self, input_output: InputOutput):
        models = self.model
        for where in self.where:
            if callable(where):
                models = self.di.call_function(where, models=models, **input_output.get_context_for_callables())
        models = models.where_for_request(
            models,
            input_output.routing_data,
            input_output.authorization_data,
            input_output,
            overrides=self.column_overrides,
        )
        limit = self.default_limit
        models = self.authorization.filter_model(models, input_output.authorization_data, input_output)
        request_data = self.map_input_to_internal_names(input_output.request_data)
        query_parameters = self.map_input_to_internal_names(input_output.query_parameters)
        pagination_data = {}
        for key in models.allowed_pagination_keys():
            if key in request_data and key in query_parameters:
                original_name = self.auto_case_internal_column_name(key)
                raise exceptions.ClientError(f"Ambiguous request: key '{original_name}' is present in both the JSON body and URL data")
            if key in request_data:
                pagination_data[key] = request_data[key]
                del request_data[key]
            if key in query_parameters:
                pagination_data[key] = query_parameters[key]
                del query_parameters[key]
        if request_data or query_parameters or pagination_data:
            self.check_request_data(request_data, query_parameters, pagination_data)
            [models, limit] = self.configure_models_from_request_data(models, request_data, query_parameters, pagination_data)
        if not models.get_query().sorts:
            models = models.sort_by(
                self.default_sort_column_name,
                self.default_sort_direction_name,
                primary_table=models.destination_name(),
            )

        return self.success(
            input_output,
            [self.model_as_json(model, input_output) for model in models],
            number_results=len(models),
            limit=limit,
            next_page=models.next_page_data(),
        )

    def configure_models_from_request_data(self, models: Model, request_data: dict[str, Any], query_parameters: dict[str, Any], pagination_data: dict[str, Any]):
        limit = int(query_parameters.get("limit", self.default_limit))
        models = models.limit(limit)
        if pagination_data:
            models = models.pagination(**pagination_data)
        sort = query_parameters.get("sort")
        direction = query_parameters.get("direction")
        if sort and direction:
            models = self.add_join(sort, models)
            [sort_column, sort_table] = self.resolve_references_for_query(sort)
            models = models.sort_by(sort_column, direction, primary_table=sort_table)

        return [models, limit]

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
                    if data["sort"][index]["column"] in sort_column_map:
                        data["sort"][index]["column"] = sort_column_map[data["sort"][index]["column"]]
            else:
                if data["sort"] in sort_column_map:
                    data["sort"] = sort_column_map[data["sort"]]

        return data

    def check_request_data(self, request_data: dict[str, Any], query_parameters: dict[str, Any], pagination_data: dict[str, Any]) -> None:
        if pagination_data:
            error = self.model.validate_pagination_kwargs(pagination_data, self.auto_case_internal_column_name)
            if error:
                raise clearskies.Exceptions.ClientError(error)
        for key in request_data.keys():
            if key not in self.allowed_request_keys or key in ["sort", "direction", "limit"]:
                raise clearskies.exceptions.ClientError(f"Invalid request parameter found in request body: '{key}'")
        for key in query_parameters.keys():
            if key not in self.allowed_request_keys:
                raise clearskies.Exceptions.ClientError(f"Invalid request parameter found in URL data: '{key}'")
            if key in request_data:
                raise clearskies.Exceptions.ClientError(f"Ambiguous request: '{key}' was found in both the request body and URL data")
        limit = query_parameters.get("limit")
        if limit is not None and type(limit) != int and type(limit) != float and type(limit) != str:
            raise clearskies.Exceptions.ClientError("Invalid request: 'limit' should be an integer")
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                raise clearskies.Exceptions.ClientError("Invalid request: 'limit' should be an integer")
        if limit and limit > self.max_limit:
            raise clearskies.Exceptions.ClientError(f"Invalid request: 'limit' must be at most {self.max_limit}")
        sort = self.from_either(request_data, query_parameters, "sort")
        direction = self.from_either(request_data, query_parameters, "direction")
        if sort and type(sort) != str:
            raise clearskies.Exceptions.ClientError("Invalid request: 'sort' should be a string")
        if direction and type(direction) != str:
            raise clearskies.Exceptions.ClientError("Invalid request: 'direction' should be a string")
        if sort or direction:
            if (sort and not direction) or (direction and not sort):
                raise clearskies.Exceptions.ClientError("You must specify 'sort' and 'direction' together in the request - not just one of them")
            if sort not in self.sortable_column_names:
                raise clearskies.Exceptions.ClientError(f"Invalid request: invalid sort column")
            if direction.lower() not in ["asc", "desc"]:
                raise clearskies.Exceptions.ClientError("Invalid request: direction must be 'asc' or 'desc'")
        self.check_search_in_request_data(request_data, query_parameters)

    def check_search_in_request_data(self, request_data: dict[str, Any], query_parameters: dict[str, Any]):
        return None

    def unpack_column_name_with_reference(self, column_name: str) -> list[str]:
        if "." not in column_name:
            return [column_name, ""]
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
        [column_name, relationship_reference] = self.unpack_column_name_with_reference(column_name)
        if not relationship_reference:
            return [column_name, self.model.destination_name()]

        return [relationship_reference, self.columns[column_name].join_table_alias()]

    def add_join(self, column_name: str, models: Model) -> Model:
        """
        Adds a join to the query for the given column name in the case where it references a column in a belongs to.

        If column_name is something like `belongs_to_column.column_name`, this will add have the belongs to column
        add it's typical join condition, so that further sorting/searching can work.

        If column_name is empty, or doesn't contain a period, then this does nothing.
        """
        if not column_name:
            return models
        [column_name, relationship_reference] = self.unpack_column_name_with_reference(column_name)
        if not relationship_reference:
            return models
        return self.columns[column_name].add_join(models)

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

        return url_parameters

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

        return json_parameters

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
