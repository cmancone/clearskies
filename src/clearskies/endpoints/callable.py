from __future__ import annotations

import inspect
from collections import OrderedDict
from typing import TYPE_CHECKING, Any
from typing import Callable as CallableType

import clearskies.configs
import clearskies.exceptions
from clearskies import authentication, autodoc, typing
from clearskies.endpoint import Endpoint
from clearskies.functional import string
from clearskies.input_outputs import InputOutput

if TYPE_CHECKING:
    from clearskies import Column, SecurityHeader
    from clearskies.authentication import Authentication, Authorization
    from clearskies.model import Model
    from clearskies.schema import Schema


class Callable(Endpoint):
    """
    An endpoint that executes a user-defined function.

    The Callable endpoint does exactly that - you provide a function that will be called when the endpoin is invoked.  Like
    all callables invoked by clearskies, you can request any defined depenndency that can be provided by the clearskies
    framework.

    Whatever you return will be returned to the client.  By default, the return value is sent along in the `data` parameter
    of the standard clearskies response.  To suppress this behavior, set `return_standard_response` to `False`.  You can also
    return an model instance, a model query, or a list of model instances and the callable endpoint will automatically return
    the columns specified in `readable_column_names` to the client.

    Here's a basic working example:

    ```python
    import clearskies


    class User(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()
        id = clearskies.columns.Uuid()
        first_name = clearskies.columns.String()
        last_name = clearskies.columns.String()
        age = clearskies.columns.Integer()


    def my_users_callable(users: User):
        bob = users.create({"first_name": "Bob", "last_name": "Brown", "age": 10})
        jane = users.create({"first_name": "Jane", "last_name": "Brown", "age": 10})
        alice = users.create({"first_name": "Alice", "last_name": "Green", "age": 10})

        return jane


    my_users = clearskies.endpoints.Callable(
        my_users_callable,
        model_class=User,
        readable_column_names=["id", "first_name", "last_name"],
    )

    wsgi = clearskies.contexts.WsgiRef(
        my_users,
        classes=[User],
    )
    wsgi()
    ```

    If you run the above script and invoke the server:

    ```bash
    $ curl 'http://localhost:8080' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "4a35a616-3d57-456f-8306-7c610a5e80e1",
            "first_name": "Jane",
            "last_name": "Brown"
        },
        "pagination": {},
        "input_errors": {}
    }
    ```

    The above example demonstrates returning a model and using readable_column_names to decide what is actually sent to the client
    (note that age is left out of the response).  The advantage of doing it this way is that clearskies can also auto-generate
    OpenAPI documentation using this strategy.  Of course, you can also just return any arbitrary data you want.  If you do return
    custom data, and also want your API to be documented, you can pass a schema along to output_schema so clearskies can document
    it:

    ```python
    import clearskies


    class DogResponse(clearskies.Schema):
        species = (clearskies.columns.String(),)
        nickname = (clearskies.columns.String(),)
        level = (clearskies.columns.Integer(),)


    clearskies.contexts.WsgiRef(
        clearskies.endpoints.Callable(
            lambda: {"species": "dog", "nickname": "Spot", "level": 100},
            output_schema=DogResponse,
        )
    )()
    ```

    """

    """
    The callable to execute when the endpoint is invoked
    """
    to_call = clearskies.configs.Callable(default=None)

    """
    A schema that describes the expected input from the client.

    Note that if this is specified it will take precedence over writeable_column_names and model_class, which
    can also be used to specify the expected input.

    ```python
    import clearskies

    class ExpectedInput(clearskies.Schema):
        first_name = clearskies.columns.String(validators=[clearskies.validators.Required()])
        last_name = clearskies.columns.String()
        age = clearskies.columns.Integer(validators=[clearskies.validators.MinimumValue(0)])

    reflect = clearskies.endpoints.Callable(
        lambda request_data: request_data,
        request_methods=["POST"],
        input_schema=ExpectedInput,
    )

    wsgi = clearskies.contexts.WsgiRef(reflect)
    wsgi()
    ```

    And then valid and invalid requests:

    ```bash
    $ curl http://localhost:8080 -d '{"first_name":"Jane","last_name":"Doe","age":1}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "first_name": "Jane",
            "last_name": "Doe",
            "age": 1
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl http://localhost:8080 -d '{"last_name":10,"age":-1,"check":"cool"}' | jq
    {
        "status": "input_errors",
        "error": "",
        "data": [],
        "pagination": {},
        "input_errors": {
            "age": "'age' must be at least 0.",
            "first_name": "'first_name' is required.",
            "last_name": "value should be a string",
            "check": "Input column check is not an allowed input column."
        }
    }
    ```

    """
    input_schema = clearskies.configs.Schema(default=None)

    """
    Whether or not the return value is meant to be wrapped up in the standard clearskies response schema.

    With the standard response schema, the return value of the function will be placed in the `data` portion of
    the standard clearskies response:

    ```python
    import clearskies

    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Callable(
            lambda: {"hello": "world"},
            return_standard_response=True, # the default value
        )
    )
    wsgi()
    ```

    Results in:

    ```bash
    $ curl http://localhost:8080 | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "hello": "world"
        },
        "pagination": {},
        "input_errors": {}
    }
    ```
    But if you want to build your own response:

    ```python
    import clearskies

    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Callable(
            lambda: {"hello": "world"},
            return_standard_response=False,
        )
    )
    wsgi()
    ```

    Results in:

    ```bash
    $ curl http://localhost:8080 | jq
    {
        "hello": "world"
    }
    ```

    Note that you can also return strings this way instead of objects/JSON.

    """
    return_standard_response = clearskies.configs.Boolean(default=True)

    """
    Set to true if the callable will be returning multiple records (used when building the auto-documentation)
    """
    return_records = clearskies.configs.Boolean(default=False)

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        to_call: CallableType,
        url: str = "",
        request_methods: list[str] = ["GET"],
        model_class: type[clearskies.model.Model] | None = None,
        readable_column_names: list[str] = [],
        writeable_column_names: list[str] = [],
        input_schema: Schema | None = None,
        output_schema: Schema | None = None,
        input_validation_callable: CallableType | None = None,
        return_standard_response: bool = True,
        return_records: bool = False,
        response_headers: list[str | CallableType[..., list[str]]] = [],
        output_map: CallableType[..., dict[str, Any]] | None = None,
        column_overrides: dict[str, Column] = {},
        internal_casing: str = "snake_case",
        external_casing: str = "snake_case",
        security_headers: list[SecurityHeader] = [],
        description: str = "",
        authentication: Authentication = authentication.Public(),
        authorization: Authorization = authentication.Authorization(),
    ):
        # we need to call the parent but don't have to pass along any of our kwargs.  They are all optional in our parent, and our parent class
        # just stores them in parameters, which we have already done.  However, the parent does do some extra initialization stuff that we need,
        # which is why we have to call the parent.
        super().__init__()

        if self.input_schema and not self.writeable_column_names:
            self.writeable_column_names = list(self.input_schema.get_columns().keys())

    def handle(self, input_output: InputOutput):
        if self.writeable_column_names or self.input_schema:
            self.validate_input_against_schema(
                self.get_request_data(input_output),
                input_output,
                self.input_schema if self.input_schema else self.model_class,
            )
        else:
            input_errors = self.find_input_errors_from_callable(input_output.request_data, input_output)
            if input_errors:
                raise clearskies.exceptions.InputErrors(input_errors)
        response = self.di.call_function(self.to_call, **input_output.get_context_for_callables())

        if not self.return_standard_response:
            return input_output.respond(response, 200)

        # did the developer return a model?
        if self.model_class and isinstance(response, self.model_class):
            # and is it a query or a single model?
            if response._data:
                return self.success(input_output, self.model_as_json(response, input_output))
            else:
                # with a query we can also get pagination data, maybe?
                converted_models = [self.model_as_json(model, input_output) for model in response]
                return self.success(
                    input_output,
                    converted_models,
                    number_results=len(response) if response.backend.can_count else None,
                    next_page=response.next_page_data(),
                )

        # or did they return a list of models?
        if isinstance(response, list) and all(isinstance(item, self.model_class) for item in response):
            return self.success(input_output, [self.model_as_json(model, input_output) for model in response])

        # if none of the above, just return the data
        return self.success(input_output, response)

    def documentation(self) -> list[autodoc.request.Request]:
        output_schema = self.output_schema if self.output_schema else self.model_class
        nice_model = string.camel_case_to_words(output_schema.__name__)

        schema_model_name = string.camel_case_to_snake_case(output_schema.__name__)
        output_data_schema = (
            self.documentation_data_schema(output_schema, self.readable_column_names)
            if self.readable_column_names
            else []
        )
        output_autodoc = (
            autodoc.schema.Object(
                self.auto_case_internal_column_name("data"),
                children=output_data_schema,
                model_name=schema_model_name if self.readable_column_names else "",
            ),
        )
        if self.return_records:
            output_autodoc.name = nice_model  # type: ignore
            output_autodoc = autodoc.schema.Array(
                self.auto_case_internal_column_name("data"),
                output_autodoc,
            )  # type: ignore

        authentication = self.authentication
        standard_error_responses = []
        if not getattr(authentication, "is_public", False):
            standard_error_responses.append(self.documentation_access_denied_response())
            if getattr(authentication, "can_authorize", False):
                standard_error_responses.append(self.documentation_unauthorized_response())
        if self.writeable_column_names:
            standard_error_responses.append(self.documentation_input_error_response())

        return [
            autodoc.request.Request(
                self.description,
                [
                    self.documentation_success_response(
                        output_autodoc,  # type: ignore
                        description=self.description,
                        include_pagination=self.return_records,
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
        if not self.writeable_column_names:
            return []

        return self.standard_json_request_parameters(self.input_schema if self.input_schema else self.model_class)

    def documentation_models(self) -> dict[str, autodoc.schema.Schema]:
        if not self.readable_column_names:
            return {}

        output_schema = self.output_schema if self.output_schema else self.model_class
        schema_model_name = string.camel_case_to_snake_case(output_schema.__name__)

        return {
            schema_model_name: autodoc.schema.Object(
                self.auto_case_internal_column_name("data"),
                children=self.documentation_data_schema(output_schema, self.readable_column_names),
            ),
        }
