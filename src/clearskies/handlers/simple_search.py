from .list import List
from .. import autodoc
class SimpleSearch(List):
    search_control_columns = ['sort', 'direction', 'limit']

    @property
    def allowed_request_keys(self):
        return [
            *self.search_control_columns,
        # the list comprehension seems unnecessary, but that is because we require searchable
        # columns to be an iterable, but that doesn't guarantee that it converts automatically
        # into a list.
            *[key for key in self.configuration('searchable_columns')],
        ]

    def check_search_in_request_data(self, request_data, query_parameters):
        for (input_source_label, input_data) in [('request body', request_data), ('URL data', query_parameters)]:
            for (column_name, value) in input_data.items():
                if column_name in self.search_control_columns:
                    continue
                if column_name not in self.configuration('searchable_columns'):
                    return f"Invalid request. An invalid search column, '{column_name}', was found in the {input_source_label}"
                [column_name, relationship_reference] = self._unpack_search_column_name(column_name)
                value_error = self._columns[column_name].check_search_value(value)
                if value_error:
                    return f"Invalid request. {value_error} for search column '{column_name}' in the {input_source_label}"

    def configure_models_from_request_data(self, models, request_data, query_parameters, pagination_data):
        [models,
         limit] = super().configure_models_from_request_data(models, request_data, query_parameters, pagination_data)
        # we can play fast and loose with the possiblity of duplicate keys because our input checking already
        # disallows that
        for input_source in [request_data, query_parameters]:
            for (column_name, value) in input_source.items():
                if column_name in self.search_control_columns:
                    continue
                if column_name == 'id':
                    column_name = self.id_column_name
                [column_name, relationship_reference] = self._unpack_search_column_name(column_name)
                column = self._columns[column_name]
                models = column.add_search(models, value, relationship_reference=relationship_reference)

        return [models, limit]

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        self._check_columns_in_configuration(configuration, 'searchable_columns')

    def documentation_request_parameters(self):
        return [
            *self.documentation_url_pagination_parameters(),
            *self.documentation_url_sort_parameters(),
            *self.documentation_url_search_parameters(),
            *self.documentation_json_search_parameters(),
        ]

    def documentation_url_search_parameters(self):
        docs = []
        for column in self._get_searchable_columns().values():
            column_doc = column.documentation()
            column_doc.name = self.auto_case_internal_column_name(column_doc.name)
            docs.append(
                autodoc.request.URLParameter(
                    column_doc,
                    description=f'Search by {column_doc.name} (via exact match)',
                )
            )
        return docs

    def documentation_json_search_parameters(self):
        docs = []
        for column in self._get_searchable_columns().values():
            column_doc = column.documentation()
            column_doc.name = self.auto_case_internal_column_name(column_doc.name)
            docs.append(
                autodoc.request.JSONBody(
                    column_doc,
                    description=f'Search by {column_doc.name} (via exact match)',
                )
            )
        return docs
