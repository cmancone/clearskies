from __future__ import annotations

import inspect
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Callable, Type

import clearskies.configs
import clearskies.exceptions
from clearskies import authentication, autodoc, typing
from clearskies.authentication import Authentication, Authorization
from clearskies.endpoint import Endpoint
from clearskies.functional import routing, string
from clearskies.input_outputs import InputOutput

if TYPE_CHECKING:
    from clearskies import Column, Schema, SecurityHeader
    from clearskies.model import Model


class Get(Endpoint):
    """
    An endpoint that fetches a single record by id (or other unique column).

    This endpoint is intended to return a single record.  You have to provide a model class, the list of columns
    to return, and (optionally) the name of the column that it should use to lookup the matching record.  If you don't
    specifically tell it what column to use to lookup the record, it will assume that you want to use the id column
    of the model.  Finally, you must declare a route parameter with a matching column name: the get endpoint will then
    fetch the desired record id out of the URL path.  Here's a simple example:

    ```python
    import clearskies


    class User(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        username = clearskies.columns.String()


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Get(
            model_class=User,
            url="/{id}",
            readable_column_names=["id", "name", "username"],
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
    $ curl 'http://localhost:8080/1-2-3-4' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "1-2-3-4",
            "name": "Bob Brown",
            "username": "bobbrown"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/1-2-3-5' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "1-2-3-5",
            "name": "Jane Doe",
            "username": "janedoe"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/notauser' | jq
    {
        "status": "client_error",
        "error": "Not Found",
        "data": [],
        "pagination": {},
        "input_errors": {}
    }
    ```
    """

    """
    Specify the name of the column that should be used to look up the record.

    If not specified, it will default to the id column name.  There must be a matching route parameter in the URL.

    ```python
    import clearskies

    class User(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        username = clearskies.columns.String()

    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Get(
            model_class=User,
            url="/{username}",
            readable_column_names=["id", "name", "username"],
            record_lookup_column_name="username",
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

    Note that `record_lookup_column_name` is set to `username` and we similarly changed the route from
    `/{id}` to `/{username}`.  We then invoke it with the username rather than the id:

    ```bash
    $ curl 'http://localhost:8080/janedoe' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "1-2-3-5",
            "name": "Jane Doe",
            "username": "janedoe"
        },
        "pagination": {},
        "input_errors": {}
    }
    ```
    """
    record_lookup_column_name = clearskies.configs.ReadableModelColumn("model_class", default=None)

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        model_class: type[Model],
        url: str,
        readable_column_names: list[str],
        record_lookup_column_name: str | None = None,
        request_methods: list[str] = ["GET"],
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
        authentication: Authentication = authentication.Public(),
        authorization: Authorization = authentication.Authorization(),
    ):
        try:
            # we will set the value for this if it isn't already set, and the easiest way is to just fetch it and see if it blows up
            self.record_lookup_column_name
        except:
            self.record_lookup_column_name = self.model_class.id_column_name

        # we need to call the parent but don't have to pass along any of our kwargs.  They are all optional in our parent, and our parent class
        # just stores them in parameters, which we have already done.  However, the parent does do some extra initialization stuff that we need,
        # which is why we have to call the parent.
        super().__init__()

        route_parameters = routing.extract_url_parameter_name_map(url)
        if self.record_lookup_column_name not in route_parameters:
            raise KeyError(
                f"Configuration error for {self.__class__.__name__} endpoint: record_lookup_column_name is set to '{self.record_lookup_column_name}' but no matching routing parameter is found"
            )

    def get_model_id(self, input_output: InputOutput) -> str:
        routing_data = input_output.routing_data
        if self.record_lookup_column_name in routing_data:
            return routing_data[self.record_lookup_column_name]
        raise KeyError(
            f"I didn't receive the ID in my routing data.  I am probably misconfigured.  My record_lookup_column_name is '{self.record_lookup_column_name}' and my route is {self.url}"
        )

    def fetch_model(self, input_output: InputOutput) -> Model:
        lookup_column_value = self.get_model_id(input_output)
        model = self.fetch_model_with_base_query(input_output).find(
            self.record_lookup_column_name + "=" + lookup_column_value
        )
        if not model:
            raise clearskies.exceptions.NotFound("Not Found")
        return model

    def handle(self, input_output: InputOutput) -> Any:
        model = self.fetch_model(input_output)
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
                    *self.documentation_routing_parameters(),
                    *self.standard_url_parameters(),
                ],
                root_properties={
                    "security": self.documentation_request_security(),
                },
            ),
        ]

    def documentation_routing_parameters(self) -> list[autodoc.request.Parameter]:
        return self.standard_url_request_parameters()

    def documentation_models(self) -> dict[str, autodoc.schema.Schema]:
        output_schema = self.output_schema if self.output_schema else self.model_class
        schema_model_name = string.camel_case_to_snake_case(output_schema.__name__)

        return {
            schema_model_name: autodoc.schema.Object(
                self.auto_case_internal_column_name("data"),
                children=self.documentation_data_schema(output_schema, self.readable_column_names),
            ),
        }
