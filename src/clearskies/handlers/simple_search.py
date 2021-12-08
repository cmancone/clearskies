from .list import List

class SimpleSearch(List):
    @property
    def allowed_request_keys(self):
        return [
            *['sort', 'start', 'limit'],
            # the list comprehension seems unnecessary, but that is because we require searchable
            # columns to be an iterable, but that doesn't guarantee that it converts automatically
            # into a list.
            *[key for key in self.configuration.get('searchable_columns'))],
        ]

    def _check_search_in_request_data(self, request_data, query_parameters):
        for (input_source_label, input_data) in [('request body', request_data), (query_parameters, 'URL data')]:
            for (column_name, value) in input_data.items():
                if column_name not in self.configuration('searchable_columns'):
                    return f"Invalid request. An invalid search column, '{column_name}', was found in the {input_source_label}"
                value_error = self._columns[column_name].check_search_value(value)
                if value_error:
                    return f"Invalid request. {value_error} for search column '{column_name}' in the {input_source_label}"

    def _configure_models_from_request_data(self, models, request_data, query_parameters):
        [models, start, limit] = super()._configure_models_from_request_data(models, request_data, query_parameters)
        # we can play fast and loose with the possiblity of duplicate keys because our input checking already
        # disallows that
        for input_source in [request_data, query_parameters]:
            for (column_name, value) in input_source.items():
                if column_name == 'id':
                    column_name = self.id_column_name
                column = self._columns[column_name]
                models = column.add_search(models, value)

        return [models, start, limit]

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        self._check_columns_in_configuration(configuration, 'searchable_columns')
