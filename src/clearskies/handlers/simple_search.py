from .list import List

class SimpleSearch(List):
    def _configure_models_from_request_data(self, models, request_data, query_parameters):
        [models, start, limit] = super()._configure_models_from_request_data(models, request_data, query_parameters)
        for (column_name, value) in query_parameters.items():
            if column_name == 'id':
                column_name = self.id_column_name
            column = self._columns[column_name]
            models = column.add_search(models, value)

        return [models, start, limit]

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
                    column_name = self.configuration('id_column')
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
