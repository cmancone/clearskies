from .simple_search import SimpleSearch
from .. import autodoc
from .. import condition_parser
class AdvancedSearch(SimpleSearch):
    expected_request_methods = 'POST'

    @property
    def allowed_request_keys(self):
        return ['sort', 'direction', 'where', 'limit']

    def configure_models_from_request_data(self, models, request_data, query_parameters, pagination_data):
        limit = int(
            self._from_either(request_data, query_parameters, 'limit', default=self.configuration('default_limit'))
        )
        models = models.limit(limit)
        if pagination_data:
            models = models.pagination(**pagination_data)
        if 'sort' in request_data:
            primary_column = request_data['sort'][0]['column']
            primary_direction = request_data['sort'][0]['direction']
            secondary_column = None
            secondary_direction = None
            if len(request_data['sort']) == 2:
                secondary_column = request_data['sort'][1]['column']
                secondary_direction = request_data['sort'][1]['direction']
            models = models.sort_by(
                primary_column,
                primary_direction,
                primary_table=models.table_name(),
                secondary_column=secondary_column,
                secondary_direction=secondary_direction,
                secondary_table=models.table_name(),
            )
        if 'where' in request_data:
            for where in request_data['where']:
                column_name = where['column']
                if column_name == 'id':
                    column_name = self.id_column_name
                [column_name, relationship_reference] = self._unpack_search_column_name(column_name)
                column = self._columns[column_name]
                models = column.add_search(
                    models,
                    where['value'],
                    operator=where['operator'].lower() if 'operator' in where else None,
                    relationship_reference=relationship_reference
                )

        return [models, limit]

    def check_request_data(self, request_data, query_parameters, pagination_data):
        # first, check the pagination data
        if pagination_data:
            error = self._model.validate_pagination_kwargs(pagination_data, self.auto_case_internal_column_name)
            if error:
                return error
        # next, check that they didn't provide something unexpected in the rest of the request
        allowed_request_keys = self.allowed_request_keys
        for key in request_data.keys():
            if key not in allowed_request_keys:
                return f"Invalid request parameter found in request body: '{key}'"
        # and ensure that the data we expect is not in the query parameters.  This is not as strict
        # of a check as ensuring that *nothing* is in the query parameters, but query parameters get
        # used for a lot of things, so that could backfire
        for key in allowed_request_keys:
            if key in query_parameters:
                return f"Invalid request: key '{key}' was found in a URL parameter but should only be in the JSON body"
        limit = request_data.get('limit', None)
        if limit is not None and type(limit) != int and type(limit) != float and type(limit) != str:
            return "Invalid request: 'limit' should be an integer"
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                return "Invalid request: 'limit' should be an integer"
        if limit and limit > self.configuration('max_limit'):
            return f"Invalid request: 'limit' must be at most {self.configuration('max_limit')}"
        allowed_sort_columns = self.configuration('sortable_columns')
        if not allowed_sort_columns:
            allowed_sort_columns = self._columns
        if 'sort' in request_data:
            if type(request_data['sort']) != list:
                return "Invalid request: if provided, 'sort' must be a list of " + \
                    "objects with 'column' and 'direction' keys"
            if len(request_data['sort']) > 2:
                return "Invalid request: at most 2 sort directives may be specified"
            for (index, sort) in enumerate(request_data['sort']):
                error_prefix = "Invalid request: 'sort' must be a list of objects with 'column' and 'direction'" + \
                    f" keys, but entry #{index+1}"
                if type(sort) != dict:
                    return f"{error_prefix} was not an object"
                if 'column' not in sort or 'direction' not in sort or not sort['column'] or not sort['direction']:
                    return f"{error_prefix} did not declare both 'column' and 'direction'"
                if len(sort) != 2:
                    return f"{error_prefix} had extra keys present"
                if sort['direction'].lower() not in ['asc', 'desc']:
                    return "Invalid request: sort direction must be 'asc' or 'desc'" + \
                        f" but found something else in sort entry #{index+1}"
                if sort['column'] not in allowed_sort_columns:
                    return f"Invalid request: invalid sort column specified in sort entry #{index+1}"
        return self.check_search_in_request_data(request_data, query_parameters)

    def check_search_in_request_data(self, request_data, query_parameters):
        if 'where' in request_data:
            if type(request_data['where']) != list:
                return "Invalid request: if provided, 'where' must be a list of objects"
            for (index, where) in enumerate(request_data['where']):
                if type(where) != dict:
                    return f"Invalid request: 'where' must be a list of objects, entry #{index+1} was not an object"
                if 'column' not in where or not where['column']:
                    return f"Invalid request: 'column' missing in 'where' entry #{index+1}"
                column_name = where['column']
                if column_name not in self.configuration('searchable_columns'):
                    return f"Invalid request: invalid search column specified in where entry #{index+1}"
                [column_name, relationship_reference] = self._unpack_search_column_name(column_name)
                if column_name == 'id':
                    column_name = self.id_column_name
                if 'value' not in where:
                    return f"Invalid request: 'value' missing in 'where' entry #{index+1}"
                operator = None
                if 'operator' in where:
                    if type(where['operator']) != str:
                        return f"Invalid request: operator must be a string in 'where' entry #{index+1}"
                    if not self._columns[column_name].is_allowed_operator(
                        where['operator'], relationship_reference=relationship_reference
                    ):
                        return f"Invalid request: given operator is not allowed for column in 'where' entry #{index+1}"
                    operator = where['operator'].lower()
                value_error = self._columns[column_name].check_search_value(
                    where['value'], operator, relationship_reference=relationship_reference
                )
                if value_error:
                    return f"Invalid request: {value_error} for 'where' entry #{index+1}"
        # similarly, query parameters mean search conditions
        for (column_name, value) in query_parameters.items():
            if column_name not in self.configuration('searchable_columns'):
                return f"Invalid request: invalid search column: '{column_name}'"
            value_error = self._columns[column_name].check_search_value(value)
            if value_error:
                return f"Invalid request: {value_error} for search column '{column_name}'"

        return None

    def map_input_to_internal_names(self, input):
        input = super().map_input_to_internal_names(input)

        # the base will take care of most of this, but it won't handle the data inside of
        # input['where'].  Therefore, we need to handle that
        if 'where' not in input or type(input['where']) != list:
            return input

        mapped_wheres = []

        # a map between the internal column name and the external column name: easier to have before hand
        search_column_map = {}
        for internal_name in self.configuration('searchable_columns'):
            external_name = self.auto_case_column_name(internal_name, True)
            search_column_map[external_name] = internal_name

        # it's important that as we do this we only change things that we know we can change.
        # we don't want to remove things that don't belong or things that seem wrong, otherwise
        # the input checking won't be able to return meaningful error messages.
        for where in input['where']:
            if type(where) != dict:
                mapped_wheres.append(where)
                continue
            mapped_where = {**where}
            for internal_name in ['column', 'operator', 'value']:
                external_name = self.auto_case_internal_column_name(internal_name)
                if external_name != internal_name and external_name in mapped_where:
                    mapped_where[internal_name] = mapped_where[external_name]
                    del mapped_where[external_name]
            if 'column' in mapped_where and type(mapped_where['column']) == str:
                if mapped_where['column'] in search_column_map:
                    mapped_where['column'] = search_column_map[mapped_where['column']]

            mapped_wheres.append(mapped_where)

        input['where'] = mapped_wheres
        return input

    def documentation_request_parameters(self):
        return [
            *self.documentation_json_parameters(),
        ]

    def documentation_json_parameters(self):
        # named 'where' in the request
        where_condition = autodoc.schema.Object(
            self.auto_case_internal_column_name('condition'),
            [
                autodoc.schema.Enum(
                    self.auto_case_internal_column_name('column'),
                    [
                        self.auto_case_column_name(column.name, True)
                        for column in self._get_searchable_columns().values()
                    ],
                    autodoc.schema.String(self.auto_case_column_name('column_name', True)),
                    example='name',
                ),
                autodoc.schema.Enum(
                    self.auto_case_internal_column_name('operator'),
                    condition_parser.ConditionParser.operators,
                    autodoc.schema.String(self.auto_case_internal_column_name('operator')),
                    example='=',
                ),
                autodoc.schema.String(self.auto_case_internal_column_name('value'), example='Jane'),
            ],
        )

        allowed_sort_columns = self.configuration('sortable_columns')
        if not allowed_sort_columns:
            allowed_sort_columns = [self.auto_case_column_name(key, True) for key in self._columns.keys()]

        sort_item = autodoc.schema.Object(
            self.auto_case_internal_column_name('sort'), [
                autodoc.schema.Enum(
                    self.auto_case_internal_column_name('column'),
                    allowed_sort_columns,
                    autodoc.schema.String(self.auto_case_internal_column_name('column')),
                    example=self.auto_case_internal_column_name('name'),
                ),
                autodoc.schema.Enum(
                    self.auto_case_internal_column_name('direction'),
                    ['asc', 'desc'],
                    autodoc.schema.String(self.auto_case_internal_column_name('direction')),
                    example='asc',
                ),
            ]
        )

        return [
            autodoc.request.JSONBody(
                autodoc.schema.Array(self.auto_case_internal_column_name('where'), where_condition),
                description='List of search conditions'
            ),
            autodoc.request.JSONBody(
                autodoc.schema.Array(self.auto_case_internal_column_name('sort'), sort_item),
                description='List of sort directives (max 2)'
            ), *self.documentation_json_pagination_parameters()
        ]
