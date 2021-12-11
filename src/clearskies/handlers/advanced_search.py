from .simple_search import SimpleSearch


class AdvancedSearch(SimpleSearch):
    def allowed_request_keys(self):
        return ['sort', 'direction', 'where', 'start', 'limit']

    def configure_models_from_request_data(self, models, request_data, query_parameters):
        start = int(self._from_either(request_data, query_parameters, 'start', default=0))
        limit = int(self._from_either(request_data, query_parameters, 'limit', default=self.configuration('default_limit')))
        models = models.limit(start, limit)
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
                secondary_column=secondary_column,
                secondary_direction=secondary_direction
            )
        if 'where' in request_data:
            for where in request_data['where']:
                column_name = where['column']
                if column_name == 'id':
                    column_name = self.id_column_name
                column = self._columns[column_name]
                models = column.add_search(
                    models,
                    where['value'],
                    operator=where['operator'].lower() if 'operator' in where else None
                )

        return [models, start, limit]

    def check_request_data(self, request_data, query_parameters):
        # first, check that they didn't provide something unexpected
        allowed_request_keys = self.allowed_request_keys()
        for key in request_data.keys():
            if key not in allowed_request_keys:
                return f"Invalid request parameter found in request body: '{key}'"
        # and ensure that the data we expect is not in the query parameters.  This is not as strict
        # of a check as ensuring that *nothing* is in the query parameters, but query parameters get
        # used for a lot of things, so that could backfire
        for key in allowed_request_keys:
            if key in query_parameters:
                return f"Invalid request: key '{key}' was found in a URL parameter but should only be in the JSON body"
        start = request_data.get('start', None)
        limit = request_data.get('limit', None)
        if start is not None and type(start) != int and type(start) != float and type(start) != str:
            return "Invalid request: 'start' should be an integer"
        if 'start' in request_data:
            try:
                start = int(start)
            except ValueError:
                return "Invalid request: 'start' should be an integer"
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

    def _check_search_in_request_data(self, request_data, query_parameters):
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
                if column_name == 'id':
                    column_name = self.id_column_name
                if 'value' not in where:
                    return f"Invalid request: 'value' missing in 'where' entry #{index+1}"
                operator = None
                if 'operator' in where:
                    if type(where['operator']) != str:
                        return f"Invalid request: operator must be a string in 'where' entry #{index+1}"
                    if not self._columns[column_name].is_allowed_operator(where['operator']):
                        return f"Invalid request: given operator is not allowed for column in 'where' entry #{index+1}"
                    operator = where['operator'].lower()
                value_error = self._columns[column_name].check_search_value(where['value'], operator)
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
