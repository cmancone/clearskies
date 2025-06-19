from __future__ import annotations

import inspect
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Callable, Type

import clearskies.configs
import clearskies.exceptions
from clearskies import authentication, autodoc, typing
from clearskies.endpoints.get import Get
from clearskies.functional import routing, string
from clearskies.input_outputs import InputOutput

if TYPE_CHECKING:
    from clearskies import SecurityHeader
    from clearskies.model import Column, Model, Schema


class Update(Get):
    """
    An endpoint to update a record.

    This endpoint handles update operations.  As with the `Get` endpoint, it will lookup the record by taking
    the record id (or any other unique column you specify) out of the URL and then will fetch that record
    using the model class.  Then, it will use the model and list of writeable column names to validate the
    incoming user input.  The default request method is `PATCH`.  If everything checks out, it will then
    update the record.

    ```python
    import clearskies


    class User(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        username = clearskies.columns.String(validators=[clearskies.validators.Required()])


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Update(
            model_class=User,
            url="/{id}",
            readable_column_names=["id", "name", "username"],
            writeable_column_names=["name", "username"],
        ),
        bindings={
            "memory_backend_default_data": [
                {
                    "model_class": User,
                    "records": [
                        {"id": "1-2-3-4", "name": "Bob Brown", "username": "bobbrown"},
                        {"id": "1-2-3-5", "name": "Jane Doe", "username": "janedoe"},
                        {"id": "1-2-3-6", "name": "Greg", "username": "greg"},
                    ],
                },
            ],
        },
    )
    wsgi()
    ```

    And when invoked:

    ```bash
    $ curl 'http://localhost:8080/1-2-3-4' -X PATCH -d '{"name": "Bobby Brown", "username": "bobbybrown"}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "1-2-3-4",
            "name": "Bobby Brown",
            "username": "bobbybrown"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/1-2-3-5' -X PATCH -d '{"name": 12345, "username": ""}' | jq
    {
        "status": "input_errors",
        "error": "",
        "data": [],
        "pagination": {},
        "input_errors": {
            "name": "value should be a string",
            "username": "'username' is required."
        }
    }
    """

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        model_class: type[Model],
        url: str,
        writeable_column_names: list[str],
        readable_column_names: list[str],
        record_lookup_column_name: str | None = None,
        input_validation_callable: Callable | None = None,
        request_methods: list[str] = ["PATCH"],
        response_headers: list[str | Callable[..., list[str]]] = [],
        output_map: Callable[..., dict[str, Any]] | None = None,
        output_schema: Schema | None = None,
        column_overrides: dict[str, Column] = {},
        internal_casing: str = "snake_case",
        external_casing: str = "snake_case",
        security_headers: list[SecurityHeader] = [],
        description: str = "",
        where: typing.condition | list[typing.condition] = [],
        joins: typing.join | list[typing.join] = [],
        authentication: authentication.Authentication = authentication.Public(),
        authorization: authentication.Authorization = authentication.Authorization(),
    ):
        # see comment in clearskies.endpoints.Create.__init__
        self.request_methods = request_methods

        # we need to call the parent but don't have to pass along any of our kwargs.  They are all optional in our parent, and our parent class
        # just stores them in parameters, which we have already done.  However, the parent does do some extra initialization stuff that we need,
        # which is why we have to call the parent.
        super().__init__(model_class, url, readable_column_names)

    def handle(self, input_output: InputOutput) -> Any:
        request_data = self.get_request_data(input_output)
        if not request_data and input_output.has_body():
            raise clearskies.exceptions.ClientError("Request body was not valid JSON")
        model = self.fetch_model(input_output)
        self.validate_input_against_schema(request_data, input_output, model)
        model.save(request_data)
        return self.success(input_output, self.model_as_json(model, input_output))

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
            *self.standard_url_request_parameters(),
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
