from .list import List
from .. import autodoc
from ..functional import string


class SimpleSearch(List):
    search_control_columns = ["sort", "direction", "limit"]

    @property
    def allowed_request_keys(self):
        return [
            *self.search_control_columns,
            # the list comprehension seems unnecessary, but that is because we require searchable
            # columns to be an iterable, but that doesn't guarantee that it converts automatically
            # into a list.
            *[key for key in self.configuration("searchable_columns")],
        ]

    def check_search_in_request_data(self, request_data, query_parameters):
        for input_source_label, input_data in [("request body", request_data), ("URL data", query_parameters)]:
            for column_name, value in input_data.items():
                if column_name in self.search_control_columns:
                    continue
                if column_name not in self.configuration("searchable_columns"):
                    return f"Invalid request. An invalid search column, '{column_name}', was found in the {input_source_label}"
                [column_name, relationship_reference] = self._unpack_column_name_with_reference(column_name)
                value_error = self._columns[column_name].check_search_value(
                    value, relationship_reference=relationship_reference
                )
                if value_error:
                    return (
                        f"Invalid request. {value_error} for search column '{column_name}' in the {input_source_label}"
                    )

    def configure_models_from_request_data(self, models, request_data, query_parameters, pagination_data):
        [models, limit] = super().configure_models_from_request_data(
            models, request_data, query_parameters, pagination_data
        )
        # we can play fast and loose with the possiblity of duplicate keys because our input checking already
        # disallows that
        for input_source in [request_data, query_parameters]:
            for column_name, value in input_source.items():
                if column_name in self.search_control_columns:
                    continue
                if column_name == "id":
                    column_name = self.id_column_name
                models = self._add_join(column_name, models)
                [column_name, relationship_reference] = self._unpack_column_name_with_reference(column_name)
                column = self._columns[column_name]
                models = column.add_search(models, value, relationship_reference=relationship_reference)

        return [models, limit]

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        self._check_columns_in_configuration(configuration, "searchable_columns")

    def _documentation_request(self, request_method, parameters):
        nice_model = string.camel_case_to_words(self._model.__class__.__name__)
        schema_model_name = string.camel_case_to_snake_case(self._model.__class__.__name__)
        data_schema = self.documentation_data_schema()

        authentication = self.configuration("authentication")
        standard_error_responses = []
        if not getattr(authentication, "is_public", False):
            standard_error_responses.append(self.documentation_access_denied_response())
            if getattr(authentication, "can_authorize", False):
                standard_error_responses.append(self.documentation_unauthorized_response())

        return autodoc.request.Request(
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
            request_methods=request_method,
            parameters=parameters,
            root_properties={
                "security": self.documentation_request_security(),
            },
        )

    def documentation(self):
        return [
            self._documentation_request(
                "GET",
                [
                    *self.documentation_url_pagination_parameters(),
                    *self.documentation_url_sort_parameters(),
                    *self.documentation_url_search_parameters(),
                ],
            ),
            self._documentation_request(
                "POST",
                [
                    *self.documentation_url_pagination_parameters(),
                    *self.documentation_url_sort_parameters(),
                    *self.documentation_json_search_parameters(),
                ],
            ),
        ]

    def documentation_url_search_parameters(self):
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
        return docs

    def documentation_json_search_parameters(self):
        docs = []
        for column in self._get_searchable_columns().values():
            column_doc = column.documentation()
            column_doc.name = self.auto_case_internal_column_name(column_doc.name)
            docs.append(
                autodoc.request.JSONBody(
                    column_doc,
                    description=f"Search by {column_doc.name} (via exact match)",
                )
            )
        return docs
