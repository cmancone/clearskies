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
    from clearskies.model import Model, Schema


class Delete(Get):
    """
    An endpoint that deletes a single record by id (or other unique column).

    This endpoint is intended to delete a single record.  You have to provide a model class and (optionally) the name
    of the column that it should use to lookup the matching record.  If you don't specifically tell it what column to
    use to lookup the record, it will assume that you want to use the id column of the model.  Finally, you must
    declare a route parameter with a matching column name: the delete endpoint will then fetch the desired record id
    out of the URL path.  The default request method is DELETE. Here's a simple example:

    ```python
    import clearskies


    class User(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        username = clearskies.columns.String()


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Delete(
            model_class=User,
            url="/{id}",
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
    $ curl 'http://localhost:8080/1-2-3-4' -X DELETE | jq
    {
        "status": "success",
        "error": "",
        "data": {},
        "pagination": {},
        "input_errors": {}
    }
    ```
    """

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        model_class: type[Model],
        url: str,
        record_lookup_column_name: str | None = None,
        response_headers: list[str | Callable[..., list[str]]] = [],
        request_methods: list[str] = ["DELETE"],
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
        super().__init__(model_class, url, [model_class.id_column_name])

    def handle(self, input_output: InputOutput) -> Any:
        model = self.fetch_model(input_output)
        model.delete()
        return self.success(input_output, {})

    def documentation(self) -> list[autodoc.request.Request]:
        output_autodoc = (autodoc.schema.Object(self.auto_case_internal_column_name("data"), children={}),)

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
                ],
                root_properties={
                    "security": self.documentation_request_security(),
                },
            ),
        ]

    def documentation_models(self) -> dict[str, autodoc.schema.Schema]:
        return {}
