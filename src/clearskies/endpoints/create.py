from __future__ import annotations
import inspect
from typing import TYPE_CHECKING, Type

from clearskies import authentication
from clearskies import autodoc
from clearskies import typing
from clearskies.endpoint import Endpoint
from collections import OrderedDict
from clearskies import autodoc
from clearskies.functional import string
from clearskies.input_outputs import InputOutput
import clearskies.configs
import clearskies.exceptions

if TYPE_CHECKING:
    from clearskies.model import Model
    from clearskies import SecurityHeader


class Create(Endpoint):
    """
    Endpoint to create a record.
    """

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        model_class: Type[Model],
        writeable_column_names: list[str],
        readable_column_names: list[str],
        input_validation_callable: callable | None = None,
        include_routing_data_in_request_data: bool = True,
        url: str = "",
        request_methods: list[str] = ["POST"],
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
        # a bit weird, but we have to do this because the default in the above definition is different than
        # the default set on the request_mehtods config in the bsae endpoint class.  parameters_to_properties will copy
        # parameters to properties, but only for things set by the developer - not for default values set in the kwarg
        # definitions.  Therefore, we always set it here to make sure we user our default, not the one in the base class.
        self.request_methods = request_methods

        # we need to call the parent but don't have to pass along any of our kwargs.  They are all optional in our parent, and our parent class
        # just stores them in parameters, which we have already done.  However, the parent does do some extra initialization stuff that we need,
        # which is why we have to call the parent.
        super().__init__()

    def handle(self, input_output: InputOutput):
        request_data = self.get_request_data(input_output)
        self.validate_input_against_schema(request_data, input_output, self.model_class)
        new_model = self.model.create(request_data, columns=self.columns)
        return self.success(input_output, self.model_as_json(new_model, input_output))

    def documentation(self) -> list[autodoc.request.Request]:
        output_schema = self.model_class
        nice_model = string.camel_case_to_words(output_schema.__name__)

        schema_model_name = string.camel_case_to_snake_case(output_schema.__name__)
        output_data_schema = self.documentation_data_schema(output_schema, self.readable_column_names)
        output_autodoc = autodoc.schema.Object(self.auto_case_internal_column_name("data"), children=output_data_schema, model_name=schema_model_name),

        authentication = self.authentication
        standard_error_responses = [self.documentation_input_error_response()]
        if not getattr(authentication, "is_public", False):
            standard_error_responses.append(self.documentation_access_denied_response())
            if getattr(authentication, "can_authorize", False):
                standard_error_responses.append(self.documentation_unauthorized_response())

        return [
            autodoc.request.Request(
                self.description,
                [
                    self.documentation_success_response(
                        output_autodoc,
                        description=self.description,
                    ),
                    *standard_error_responses,
                    self.documentation_generic_error_response(),
                ],
                relative_path=self.url,
                request_methods=self.request_methods,
                parameters=[
                    *self.documentation_request_parameters(),
                    *self.standard_url_parameters(),
                ],
                root_properties={
                    "security": self.documentation_request_security(),
                },
            ),
        ]

    def documentation_request_parameters(self) -> list[Parameter]:
        return [
            *self.standard_json_request_parameters(self.model_class),
            *(self.standard_url_request_parameters() if self.include_routing_data_in_request_data else []),
        ]

    def documentation_models(self) -> dict[str, autodoc.schema.Schema]:
        output_schema = self.output_schema if self.output_schema else self.model_class
        schema_model_name = string.camel_case_to_snake_case(output_schema.__name__)

        return {
            schema_model_name: autodoc.schema.Object(
                self.auto_case_internal_column_name("data"),
                children=self.documentation_data_schema(output_schema, self.readable_column_names),
            ),
        }
