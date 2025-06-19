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
    from clearskies import Column, SecurityHeader
    from clearskies.model import Model


class Create(Endpoint):
    """
    An endpoint to create a record.

    This endpoint accepts user input and uses it to create a record for the given model class.  You have
    to provide the model class, which columns the end-user can set, and which columns get returned
    to the client.  The column definitions in the model class are used to strictly validate the user
    input.  Here's a basic example of a model class with the create endpoint in use:

    ```python
    import clearskies
    from clearskies import validators, columns


    class MyAwesomeModel(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = columns.Uuid()
        name = clearskies.columns.String(
            validators=[
                validators.Required(),
                validators.MaximumLength(50),
            ]
        )
        email = columns.Email(validators=[validators.Unique()])
        some_number = columns.Integer()
        expires_at = columns.Date()
        created_at = columns.Created()


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Create(
            MyAwesomeModel,
            readable_column_names=["id", "name", "email", "some_number", "expires_at", "created_at"],
            writeable_column_names=["name", "email", "some_number", "expires_at"],
        ),
    )
    wsgi()
    ```

    The following shows how to invoke it, and demonstrates the strict input validation that happens as part of the
    process:

    ```bash
    $ curl 'http://localhost:8080/' -d '{"name":"Example", "email":"test@example.com","some_number":5,"expires_at":"2024-12-31"}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "74eda1c6-fe66-44ec-9246-758d16e1a304",
            "name": "Example",
            "email": "test@example.com",
            "some_number": 5,
            "expires_at": "2024-12-31",
            "created_at": "2025-05-23T16:36:30+00:00"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/' -d '{"name":"", "email":"test@example.com","some_number":"asdf","expires_at":"not-a-date", "not_a_column": "sup"}' | jq
    {
        "status": "input_errors",
        "error": "",
        "data": [],
        "pagination": {},
        "input_errors": {
            "name": "'name' is required.",
            "email": "Invalid value for 'email': the given value already exists, and must be unique.",
            "some_number": "value should be an integer",
            "expires_at": "given value did not appear to be a valid date",
            "not_a_column": "Input column not_a_column is not an allowed input column."
        }
    }
    ```

    The first call successfully creates a new record.  The second call fails with a variety of error messages:

     1. A name wasn't provided by the model class marked this as required
     2. We provided the same email address again, but this column is marked as unique
     3. The number provided in `some_number` wasn't actually a number
     4. The provided value for `expires_at` wasn't actually a date.
     5. We provided an extra column (`not_a_column`) that wasn't in the list of allowed columns.
    """

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        model_class: type[Model],
        writeable_column_names: list[str],
        readable_column_names: list[str],
        input_validation_callable: Callable | None = None,
        include_routing_data_in_request_data: bool = False,
        url: str = "",
        request_methods: list[str] = ["POST"],
        response_headers: list[str | Callable[..., list[str]]] = [],
        output_map: Callable[..., dict[str, Any]] | None = None,
        output_schema: clearskies.Schema | None = None,
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

    def handle(self, input_output: InputOutput) -> Any:
        request_data = self.get_request_data(input_output)
        if not request_data and input_output.has_body():
            raise clearskies.exceptions.ClientError("Request body was not valid JSON")
        self.validate_input_against_schema(request_data, input_output, self.model_class)
        new_model = self.model.create(request_data, columns=self.columns)
        return self.success(input_output, self.model_as_json(new_model, input_output))

    def documentation(self) -> list[autodoc.request.Request]:
        output_schema = self.model_class
        nice_model = string.camel_case_to_words(output_schema.__name__)

        schema_model_name = string.camel_case_to_snake_case(output_schema.__name__)
        output_data_schema = self.documentation_data_schema(output_schema, self.readable_column_names)
        output_autodoc = (
            autodoc.schema.Object(
                self.auto_case_internal_column_name("data"), children=output_data_schema, model_name=schema_model_name
            ),
        )

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
                        output_autodoc,  # type: ignore
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

    def documentation_request_parameters(self) -> list[autodoc.request.Parameter]:
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
