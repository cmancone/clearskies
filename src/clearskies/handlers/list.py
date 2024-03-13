from .base import Base
from collections import OrderedDict
from .. import autodoc
from ..functional import string
import inspect
from ..column_types import BelongsTo


class List(Base):
    _model = None
    _columns = None
    _searchable_columns = None
    _readable_columns = None
    _prepared_models = None
    expected_request_methods = "GET"

    _configuration_defaults = {
        "model": None,
        "model_class": None,
        "readable_columns": None,
        "searchable_columns": None,
        "sortable_columns": [],
        "where": [],
        "join": [],
        "group_by": "",
        "default_sort_column": "",
        "default_sort_direction": "asc",
        "default_limit": 100,
        "max_limit": 200,
    }

    def __init__(self, di):
        super().__init__(di)

    def handle(self, input_output):
        models = self._prepared_models.clone()
        for where in self.configuration("where"):
            if callable(where):
                models = self._di.call_function(
                    where, models=models, input_output=input_output, routing_data=input_output.routing_data()
                )
        models = models.where_for_request(
            models,
            input_output.routing_data(),
            input_output.get_authorization_data(),
            input_output,
        )
        limit = self.configuration("default_limit")
        authorization = self._configuration.get("authorization", None)
        if authorization and hasattr(authorization, "filter_models"):
            models = authorization.filter_models(models, input_output.get_authorization_data(), input_output)
        request_data = self.map_input_to_internal_names(input_output.request_data(False))
        query_parameters = self.map_input_to_internal_names(input_output.get_query_parameters())
        pagination_data = {}
        for key in self._model.allowed_pagination_keys():
            if key in request_data and key in query_parameters:
                original_name = self.auto_case_internal_column_name(key)
                return self.error(
                    input_output,
                    f"Ambiguous request: key '{original_name}' is present in both the JSON body and URL data",
                )
            if key in request_data:
                pagination_data[key] = request_data[key]
                del request_data[key]
            if key in query_parameters:
                pagination_data[key] = query_parameters[key]
                del query_parameters[key]
        if request_data or query_parameters or pagination_data:
            error = self.check_request_data(request_data, query_parameters, pagination_data)
            if error:
                return self.error(input_output, error, 400)
            [models, limit] = self.configure_models_from_request_data(
                models, request_data, query_parameters, pagination_data
            )
        if not models.query_sorts:
            models = models.sort_by(
                self.configuration("default_sort_column"),
                self.configuration("default_sort_direction"),
                primary_table=models.table_name(),
            )

        return self.success(
            input_output,
            [self._model_as_json(model, input_output) for model in models],
            number_results=len(models),
            limit=limit,
            next_page=models.next_page_data(),
        )

    def configure_models_from_request_data(self, models, request_data, query_parameters, pagination_data):
        limit = int(query_parameters.get("limit", self.configuration("default_limit")))
        models = models.limit(limit)
        if pagination_data:
            models = models.pagination(**pagination_data)
        sort = query_parameters.get("sort")
        direction = query_parameters.get("direction")
        if sort and direction:
            models = self._add_join(sort, models)
            [sort_column, sort_table] = self._resolve_references_for_query(sort)
            models = models.sort_by(sort_column, direction, primary_table=sort_table)

        return [models, limit]

    @property
    def allowed_request_keys(self):
        return ["sort", "direction", "limit"]

    @property
    def internal_request_keys(self):
        return ["sort", "direction", "limit"]

    def map_input_to_internal_names(self, input):
        internal_request_keys = [*self.internal_request_keys, *self._model.allowed_pagination_keys()]
        for key in internal_request_keys:
            mapped_key = self.auto_case_internal_column_name(key)
            if mapped_key != key and mapped_key in input:
                input[key] = input[mapped_key]
                del input[mapped_key]
        # any non-internal fields are assumed to be column names and need to go
        # through the full mapping
        for key in set(self.allowed_request_keys) - set(internal_request_keys):
            mapped_key = self.auto_case_column_name(key, True)
            if mapped_key != key and mapped_key in input:
                input[key] = input[mapped_key]
                del input[mapped_key]

        # finally, if we have a sort key set then convert the value to the properly cased column name
        if "sort" in input:
            # we can't just take the sort value and convert it to internal casing because camel/title case
            # to snake_case can be ambiguous (while snake_case to camel/title is not)
            sort_column_map = {}
            for internal_name in self.configuration("sortable_columns"):
                external_name = self.auto_case_column_name(internal_name, True)
                sort_column_map[external_name] = internal_name
            # sometimes the sort may be a list of directives
            if type(input["sort"]) == list:
                for index, sort_entry in enumerate(input["sort"]):
                    if input["sort"][index]["column"] in sort_column_map:
                        input["sort"][index]["column"] = sort_column_map[input["sort"][index]["column"]]
            else:
                if input["sort"] in sort_column_map:
                    input["sort"] = sort_column_map[input["sort"]]

        return input

    def check_request_data(self, request_data, query_parameters, pagination_data):
        if pagination_data:
            error = self._model.validate_pagination_kwargs(pagination_data, self.auto_case_internal_column_name)
            if error:
                return error
        for key in request_data.keys():
            if key not in self.allowed_request_keys or key in ["sort", "direction", "limit"]:
                return f"Invalid request parameter found in request body: '{key}'"
        for key in query_parameters.keys():
            if key not in self.allowed_request_keys:
                return f"Invalid request parameter found in URL data: '{key}'"
            if key in request_data:
                return f"Ambiguous request: '{key}' was found in both the request body and URL data"
        limit = query_parameters.get("limit")
        if limit is not None and type(limit) != int and type(limit) != float and type(limit) != str:
            return "Invalid request: 'limit' should be an integer"
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                return "Invalid request: 'limit' should be an integer"
        if limit and limit > self.configuration("max_limit"):
            return f"Invalid request: 'limit' must be at most {self.configuration('max_limit')}"
        allowed_sort_columns = self.configuration("sortable_columns")
        if not allowed_sort_columns:
            allowed_sort_columns = self._columns
        sort = self._from_either(request_data, query_parameters, "sort")
        direction = self._from_either(request_data, query_parameters, "direction")
        if sort and type(sort) != str:
            return "Invalid request: 'sort' should be a string"
        if direction and type(direction) != str:
            return "Invalid request: 'direction' should be a string"
        if sort or direction:
            if (sort and not direction) or (direction and not sort):
                return "You must specify 'sort' and 'direction' together in the request - not just one of them"
            if sort not in allowed_sort_columns:
                return f"Invalid request: invalid sort column"
            if direction.lower() not in ["asc", "desc"]:
                return "Invalid request: direction must be 'asc' or 'desc'"
        return self.check_search_in_request_data(request_data, query_parameters)

    def check_search_in_request_data(self, request_data, query_parameters):
        return None

    def _unpack_column_name_with_reference(self, column_name):
        if "." not in column_name:
            return [column_name, ""]
        return column_name.split(".", 1)

    def configure(self, configuration):
        super().configure(configuration)
        # performance optimizations! First, take any of our configuration options that affect
        # the search results and create a models class with those built in
        self._prepared_models = self._model
        for where in self.configuration("where"):
            if type(where) == str:
                self._prepared_models = self._prepared_models.where(where)
        for join in self.configuration("join"):
            self._prepared_models = self._prepared_models.join(join)
        if self.configuration("group_by"):
            self._prepared_models = self._prepared_models.group_by(self.configuration("group_by"))
        self._prepared_models = self._prepared_models.limit(self.configuration("default_limit"))

        if self._prepared_models.supports_n_plus_one():
            for column in self._get_readable_columns().values():
                self._prepared_models = column.configure_n_plus_one(self._prepared_models)

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        error_prefix = "Configuration error for %s:" % (self.__class__.__name__)
        has_model_class = ("model_class" in configuration) and configuration["model_class"] is not None
        has_model = ("model" in configuration) and configuration["model"] is not None
        if not has_model and not has_model_class:
            raise KeyError(f"{error_prefix} you must specify 'model' or 'model_class'")
        if has_model and has_model_class:
            raise KeyError(f"{error_prefix} you specified both 'model' and 'model_class', but can only provide one")
        if has_model and inspect.isclass(configuration["model"]):
            raise ValueError(
                "{error_prefix} you must provide a model instance in the 'model' configuration setting, but a class was provided instead"
            )
        self._model = self._di.build(configuration["model_class"]) if has_model_class else configuration["model"]
        self._columns = self._model.columns(overrides=configuration.get("column_overrides"))
        model_class_name = self._model.__class__.__name__
        # checks for searchable_columns and readable_columns
        self._check_columns_in_configuration(configuration, "readable_columns")
        # the List base class doesn't use searchable columns so just ignore this check for List
        if type(self) != List:
            self._check_columns_in_configuration(configuration, "searchable_columns")

        if "default_sort_column" not in configuration:
            raise ValueError(f"{error_prefix} missing required configuration 'default_sort_column'")

        # sortable_columns, wheres, and joins should all be iterables
        for config_name, contents in {
            "sortable_columns": "column names",
            "where": "conditions",
            "join": "joins",
        }.items():
            if config_name not in configuration:
                continue
            if not hasattr(configuration[config_name], "__iter__") or type(configuration[config_name]) == str:
                raise ValueError(
                    f"{error_prefix} '{config_name}' should be an iterable of {contents} "
                    + f", not {str(type(configuration[config_name]))}"
                )

        # checks for sortable_columns
        if configuration.get("sortable_columns"):
            self._check_columns_in_configuration(configuration, "searchable_columns")

        # common checks for group_by and default_sort_column
        for config_name in ["group_by", "default_sort_column"]:
            value = configuration.get(config_name)
            if not value:
                continue
            # we're being lazy for now and not checking complicated values
            if "." in value:
                continue
            if value not in self._columns:
                raise ValueError(
                    f"{error_prefix} '{config_name}' references column named {column_name} "
                    + f"but this column does not exist for model '{model_class_name}'"
                )

        for config_name in ["default_page_length", "max_page_length"]:
            if config_name in configuration and type(configuration[config_name]) != int:
                raise ValueError(
                    f"{error_prefix} '{config_name}' should be an int, not {str(type(configuration[config_name]))}"
                )

    def _check_columns_in_configuration(self, configuration, config_name):
        error_prefix = "Configuration error for %s:" % (self.__class__.__name__)
        model_class_name = self._model.__class__.__name__
        if not configuration.get(config_name):
            raise ValueError(f"{error_prefix} missing required configuration '{config_name}'")
        if not hasattr(configuration[config_name], "__iter__"):
            raise ValueError(
                f"{error_prefix} '{config_name}' should be an iterable of column names "
                + f", not {str(type(configuration[config_name]))}"
            )
        for column_name in configuration[config_name]:
            relationship_reference = None
            if config_name == "searchable_columns" or config_name == "sortable_columns":
                [column_name, relationship_reference] = self._unpack_column_name_with_reference(column_name)
            if column_name not in self._columns:
                raise ValueError(
                    f"{error_prefix} '{config_name}' references column named {column_name} "
                    + f"but this column does not exist for model '{model_class_name}'"
                )
            column = self._columns[column_name]
            if config_name == "readable_columns" and not column.is_readable:
                raise ValueError(
                    f"{error_prefix} '{config_name}' references column named {column_name} "
                    + f"but this column does not exist for model '{model_class_name}'"
                )
            if relationship_reference:
                if not isinstance(column, BelongsTo):
                    raise ValueError(
                        f"{error_prefix} '{config_name}' references {column_name}.{relationship_reference}. "
                        + f"For this to work, {column_name} must be a belongs to relatiionship, but it isn't."
                    )
                if relationship_reference not in column.parent_columns:
                    parent_class = column.config("parent_models_class").__name__
                    raise ValueError(
                        f"{error_prefix} '{config_name}' references {column_name}.{relationship_reference}, "
                        + f"but {relationship_reference} is not a valid column in the BelongsTo model class, {parent_class}."
                    )

    def _resolve_references_for_query(self, column_name):
        """
        Takes the column name and returns the name and table.

        If it's just a column name, we assume the table is the table for our model class.
        If it's something like `belongs_to_column.column_name`, then it will find the appropriate
        table reference.
        """
        if not column_name:
            return [None, None]
        [column_name, relationship_reference] = self._unpack_column_name_with_reference(column_name)
        if not relationship_reference:
            return [column_name, self._model.table_name()]

        belongs_to_column = self._columns[column_name]
        return [relationship_reference, belongs_to_column.join_table_alias()]

    def _add_join(self, column_name, models):
        """
        Adds a join to the query for the given column name in the case where it references a column in a belongs to.

        If column_name is something like `belongs_to_column.column_name`, this will add have the belongs to column
        add it's typical join condition, so that further sorting/searching can work.

        If column_name is empty, or doesn't contain a period, then this does nothing.
        """
        if not column_name:
            return models
        [column_name, relationship_reference] = self._unpack_column_name_with_reference(column_name)
        if not relationship_reference:
            return models
        return self._columns[column_name].add_join(models)

    def _from_either(self, request_data, query_parameters, key, default=None, ignore_none=True):
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

    def _get_columns(self, column_type):
        resolved_columns = OrderedDict()
        for column_name in self.configuration(f"{column_type}_columns"):
            if column_type == "searchable":
                [column_name, relationship_reference] = self._unpack_column_name_with_reference(column_name)
            if column_name not in self._columns:
                class_name = self.__class__.__name__
                model_class = self._model.__class__.__name__
                raise ValueError(
                    f"Handler {class_name} was configured with {column_type} column '{column_name}' but this "
                    + f"column doesn't exist for model {model_class}"
                )
            resolved_columns[column_name] = self._columns[column_name]
        return resolved_columns

    def _get_readable_columns(self):
        if self._readable_columns is None:
            self._readable_columns = self._get_columns("readable")
        return self._readable_columns

    def _get_searchable_columns(self):
        if self._searchable_columns is None:
            self._searchable_columns = self._get_columns("searchable")
        return self._searchable_columns

    def documentation(self):
        nice_model = string.camel_case_to_words(self._model.__class__.__name__)
        schema_model_name = string.camel_case_to_snake_case(self._model.__class__.__name__)
        data_schema = self.documentation_data_schema()

        authentication = self.configuration("authentication")
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
                relative_path=self.configuration("base_url"),
                request_methods=self.expected_request_methods,
                parameters=self.documentation_request_parameters(),
                root_properties={
                    "security": self.documentation_request_security(),
                },
            ),
        ]

    def documentation_request_parameters(self):
        return [
            *self.documentation_url_pagination_parameters(),
            *self.documentation_url_sort_parameters(),
        ]

    def documentation_models(self):
        schema_model_name = string.camel_case_to_snake_case(self._model.__class__.__name__)

        return {
            schema_model_name: autodoc.schema.Object(
                self.auto_case_internal_column_name("data"),
                children=self.documentation_data_schema(),
            ),
        }

    def documentation_id_url_parameter(self):
        id_column_name = self.id_column_name
        if id_column_name in self._columns:
            id_column_schema = self._columns[id_column_name].documentation()
        else:
            id_column_schema = autodoc.schema.Integer(self.auto_case_internal_column_name("id"))
        return autodoc.request.URLPath(
            id_column_schema,
            description="The id of the record to fetch",
            required=True,
        )

    def documentation_url_pagination_parameters(self):
        url_parameters = [
            autodoc.request.URLParameter(
                autodoc.schema.Integer(self.auto_case_internal_column_name("limit")),
                description="The number of records to return",
            ),
        ]

        for parameter in self._model.documentation_pagination_parameters(self.auto_case_internal_column_name):
            (schema, description) = parameter
            url_parameters.append(autodoc.request.URLParameter(schema, description=description))

        return url_parameters

    def documentation_url_sort_parameters(self):
        sort_columns = self.configuration("sortable_columns")
        if not sort_columns:
            sort_columns = self._columns.keys()
        sort_columns = [self.auto_case_column_name(internal_name, True) for internal_name in sort_columns]
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

    def documentation_json_pagination_parameters(self):
        json_parameters = [
            autodoc.request.JSONBody(
                autodoc.schema.Integer(self.auto_case_internal_column_name("limit")),
                description="The number of records to return",
            ),
        ]

        for parameter in self._model.documentation_pagination_parameters(self.auto_case_internal_column_name):
            (schema, description) = parameter
            json_parameters.append(autodoc.request.JSONBody(schema, description=description))

        return json_parameters

    def documentation_json_sort_parameters(self):
        sort_columns = self.configuration("sortable_columns")
        if not sort_columns:
            sort_columns = self._columns.keys()
        sort_columns = [self.auto_case_column_name(internal_name, True) for internal_name in sort_columns]
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
