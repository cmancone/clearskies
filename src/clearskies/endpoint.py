from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING
import urllib.parse
from collections import OrderedDict

from clearskies.autodoc.request import Request, Parameter
from clearskies.autodoc.response import Response
from clearskies.autodoc import schema
import clearskies.column
import clearskies.configurable
import clearskies.configs
import clearskies.di
import clearskies.parameters_to_properties
import clearskies.typing
from clearskies import exceptions
from clearskies.authentication import Authentication, Authorization, Public
from clearskies.functional import string, routing

if TYPE_CHECKING:
    from clearskies import Column, Model, SecurityHeader
    from clearskies.input_output import InputOutput
    from clearskies.schema import Schema

class Endpoint(clearskies.configurable.Configurable, clearskies.di.InjectableProperties):
    """
    Endpoints - the clearskies workhorse.

    With clearskies, endpoints exist to offload some drudgery and make your life easier, but they can also
    get out of your way when you don't need them.  Think of them as pre-built endpoints that can execute
    common functionality needed for web applications/APIs.  Instead of defining a function that fetches
    records from your backend and returns them to the end user, you can let the list endpoint do this for you
    with a minimal amount of configuration.  Instead of making an endpoint that creates records, just deploy
    a create endpoint.  Each endpoint has their own configuration settings, but there are some configuration
    settings that are common to all endpoints, which are listed below:

    ## Url

    The URL for the endpoint.  Note that this is a relative URL.  If the endpoint is attached directly to a context,
    then it will become the exact path to execute the endpoint.  Endpoints can also be attached to endpoint groups,
    which have their own URL prefixes, in which case the endpoint

    """

    """
    The dependency injection container
    """
    di = clearskies.di.inject.Di()

    """
    Whether or not this endpoint can handle CORS
    """
    has_cors = False

    """
    The actual CORS header
    """
    cors_header: SecurityHeader | None = None

    """
    Set some response headers that should be returned for this endpoint.

    Provide a list of response headers to return to the caller when this endpoint is executed.
    This should be given a list containing a combination of strings or callables that return a list of strings.
    The strings in question should be headers formatted as "key: value".  If you attach a callable, it can accept
    any of the standard dependencies or context-specific values like any other callable in a clearskies
    application:

    ```
    def custom_headers(query_parameters):
        some_value = "yes" if query_parameters.get("stuff") else "no"
        return [f"x-custom: {some_value}", "content-type: application/custom"]

    endpoint = clearskies.endpoints.Callable(
        lambda: {"hello": "world"},
        response_headers=custom_headers,
    )

    wsgi = clearskies.contexts.WsgiRef(endpoint)
    wsgi()
    ```
    """
    response_headers = clearskies.configs.StringListOrCallable(default=[])

    """
    Set the URL for the endpoint

    When an endpoint is attached directly to a context, then the endpoint's URL becomes the exact URL
    to invoke the endpoint.  If it is instead attached to an endpoint group, then the URL of the endpoint
    becomes a suffix on the URL of the group.  This is described in more detail in the documentation for endpoint
    groups, so here's an example of attaching endpoints directly and setting the URL:

    ```
    import clearskies

    endpoint = clearskies.endpoints.Callable(
        lambda: {"hello": "World"},
        url="/hello/world",
    )

    wsgi = clearskies.contexts.WsgiRef(endpoint)
    wsgi()
    ```

    Which then acts as expected:

    ```
    $ curl 'http://localhost:8080/hello/asdf' | jq
    {
        "status": "client_error",
        "error": "Not Found",
        "data": [],
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/hello/world' | jq
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

    Some endpoints allow or require the use of named routing parameters.  Named routing paths are created using either the
    `/{name}/` syntax or `/:name/`.  These parameters can be injected into any callable via the `routing_data`
    dependency injection name, as well as via their name:

    ```
    import clearskies

    endpoint = clearskies.endpoints.Callable(
        lambda first_name, last_name: {"hello": f"{first_name} {last_name}"},
        url="/hello/:first_name/{last_name}",
    )

    wsgi = clearskies.contexts.WsgiRef(endpoint)
    wsgi()
    ```

    Which you can then invoke in the usual way:

    ```
    $ curl 'http://localhost:8080/hello/bob/brown' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "hello": "bob brown"
        },
        "pagination": {},
        "input_errors": {}
    }

    ```

    """
    url = clearskies.configs.Url(default="")

    """
    The allowed request methods for this endpoint.

    By default, only GET is allowed.

    ```
    import clearskies

    endpoint = clearskies.endpoints.Callable(
        lambda: {"hello": "world"},
        request_methods=["POST"],
    )

    wsgi = clearskies.contexts.WsgiRef(endpoint)
    wsgi()
    ```

    And to execute:

    ```
    $ curl 'http://localhost:8080/' -X POST | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "hello": "world"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080/' -X GET | jq
    {
        "status": "client_error",
        "error": "Not Found",
        "data": [],
        "pagination": {},
        "input_errors": {}
    }
    ```
    """
    request_methods = clearskies.configs.SelectList(allowed_values=["GET", "POST", "PUT", "DELETE", "PATCH"], default=["GET"])

    """
    The authentication for this endpoint (default is public)

    Use this to attach an instance of `clearskies.authentication.Authentication` to an endpoint, which enforces authentication.
    For more details, see the dedicated documentation section on authentication and authorization. By default, all endpoints are public.
    """
    authentication = clearskies.configs.Authentication(default=Public())

    """
    The authorization rules for this endpoint

    Use this to attach an instance of `clearskies.authentication.Authorization` to an endpoint, which enforces authorization.
    For more details, see the dedicated documentation section on authentication and authorization. By default, no authorization is enforced.
    """
    authorization = clearskies.configs.Authorization(default=Authorization())

    """
    An override of the default model-to-json mapping for endpoints that auto-convert models to json.

    Many endpoints allow you to return a model which is then automatically converted into a JSON response.  When this is the case,
    you can provide a callable in the `output_map` parameter which will be called instead of following the usual method for
    JSON conversion.  Note that if you use this method, you should also specify `output_schema`, which the autodocumentation
    will then use to document the endpoint.

    Your function can request any named dependency injection parameter as well as the standard context parameters for the request.

    ```
    import clearskies
    import datetime
    from dateutil.relativedelta import relativedelta

    class User(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        dob = clearskies.columns.Datetime()

    class UserResponse(clearskies.Schema):
        id = clearskies.columns.String()
        name = clearskies.columns.String()
        age = clearskies.columns.Integer()
        is_special = clearskies.columns.Boolean()

    def user_to_json(model: User, utcnow: datetime.datetime, special_person: str):
        return {
            "id": model.id,
            "name": model.name,
            "age": relativedelta(utcnow, model.dob).years,
            "is_special": model.name.lower() == special_person.lower(),
        }

    list_users = clearskies.endpoints.List(
        model_class=User,
        url="/{special_person}",
        output_map = user_to_json,
        output_schema = UserResponse,
        readable_column_names=["id", "name"],
        sortable_column_names=["id", "name", "dob"],
        default_sort_column_name="dob",
        default_sort_direction="DESC",
    )

    wsgi = clearskies.contexts.WsgiRef(
        list_users,
        classes=[User],
        bindings={
            "special_person": "jane",
            "memory_backend_default_data": [
                {
                    "model_class": User,
                    "records": [
                        {"id": "1-2-3-4", "name": "Bob", "dob": datetime.datetime(1990, 1, 1)},
                        {"id": "1-2-3-5", "name": "Jane", "dob": datetime.datetime(2020, 1, 1)},
                        {"id": "1-2-3-6", "name": "Greg", "dob": datetime.datetime(1980, 1, 1)},
                    ]
                },
            ]
        }
    )
    wsgi()
    ```

    Which gives:

    ```
    $ curl 'http://localhost:8080/jane' | jq
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "1-2-3-5",
                "name": "Jane",
                "age": 5,
                "is_special": true
            }
            {
                "id": "1-2-3-4",
                "name": "Bob",
                "age": 35,
                "is_special": false
            },
            {
                "id": "1-2-3-6",
                "name": "Greg",
                "age": 45,
                "is_special": false
            },
        ],
        "pagination": {
            "number_results": 3,
            "limit": 50,
            "next_page": {}
        },
        "input_errors": {}
    }

    ```

    """
    output_map = clearskies.configs.Callable(default=None)

    """
    A schema that describes the expected output to the client.

    This is used to build the auto-documentation.  See the documentation for clearskies.endpoint.output_map for examples.
    Note that this is typically not required - when returning models and relying on clearskies to auto-convert to JSON,
    it will also automatically generate your documentation.
    """
    output_schema = clearskies.configs.Schema(default=None)

    """
    The model class used by this endpoint.

    The majority of endpoints require a model class that tells the endpoint where to get/save its data.
    """
    model_class = clearskies.configs.ModelClass(default=None)

    """
    Columns from the model class that should be returned to the client.

    Most endpoints use a model to build the return response to the user.  In this case, `readable_column_names`
    instructs the model what columns should be sent back to the user.  This information is similarly used when generating
    the documentation for the endpoint.

    ```
    import clearskies

    class User(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        secret = clearskies.columns.String()

    list_users = clearskies.endpoints.List(
        model_class=User,
        readable_column_names=["id", "name"],
        sortable_column_names=["id", "name"],
        default_sort_column_name="name",
    )

    wsgi = clearskies.contexts.WsgiRef(
        list_users,
        classes=[User],
        bindings={
            "memory_backend_default_data": [
                {
                    "model_class": User,
                    "records": [
                        {"id": "1-2-3-4", "name": "Bob", "secret": "Awesome dude"},
                        {"id": "1-2-3-5", "name": "Jane", "secret": "Gets things done"},
                        {"id": "1-2-3-6", "name": "Greg", "secret": "Loves chocolate"},
                    ]
                },
            ]
        }
    )
    wsgi()
    ```

    And then:

    ```
    $ curl 'http://localhost:8080'
    {
        "status": "success",
        "error": "",
        "data": [
            {
                "id": "1-2-3-4",
                "name": "Bob"
            },
            {
                "id": "1-2-3-6",
                "name": "Greg"
            },
            {
                "id": "1-2-3-5",
                "name": "Jane"
            }
        ],
        "pagination": {
            "number_results": 3,
            "limit": 50,
            "next_page": {}
        },
        "input_errors": {}
    }

    ```
    """
    readable_column_names = clearskies.configs.ReadableModelColumns("model_class", default=[])

    """
    Specifies which columns from a model class can be set by the client.

    Many endpoints allow or require input from the client.  The most common way to provide input validation
    is by setting the model class and using `writeable_column_names` to specify which columns the end client can
    set.  Clearskies will then use the model schema to validate the input and also auto-generate documentation
    for the endpoint.

    ```
    import clearskies

    class User(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String(validators=[clearskies.validators.Required()])
        date_of_birth = clearskies.columns.Date()

    send_user = clearskies.endpoints.Callable(
        lambda request_data: request_data,
        request_methods=["GET","POST"],
        writeable_column_names=["name", "date_of_birth"],
        model_class=User,
    )

    wsgi = clearskies.contexts.WsgiRef(send_user)
    wsgi()
    ```

    If we send a valid payload:

    ```
    $ curl 'http://localhost:8080' -d '{"name":"Jane","date_of_birth":"01/01/1990"}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "name": "Jane",
            "date_of_birth": "01/01/1990"
        },
        "pagination": {},
        "input_errors": {}
    }
    ```

    And we can see the automatic input validation by sending some incorrect data:

    ```
    $ curl 'http://localhost:8080' -d '{"name":"","date_of_birth":"this is not a date","id":"hey"}' | jq
    {
        "status": "input_errors",
        "error": "",
        "data": [],
        "pagination": {},
        "input_errors": {
            "name": "'name' is required.",
            "date_of_birth": "given value did not appear to be a valid date",
            "other_column": "Input column other_column is not an allowed input column."
        }
    }
    ```

    """
    writeable_column_names = clearskies.configs.WriteableModelColumns("model_class", default=[])

    """
    Columns from the model class that can be searched by the client.

    Sets which columns the client is allowed to search (for endpoints that support searching).
    """
    searchable_column_names = clearskies.configs.SearchableModelColumns("model_class", default=[])

    """
    A function to call to add custom input validation logic.

    Typically, input validation happens by choosing the appropriate column in your schema and adding validators where necessary.  You
    can also create custom columns with their own input validation logic.  However, if desired, endpoints that accept user input also
    allow you to add callables for custom validation logic.  These functions should return a dictionary where the key name
    represents the name of the column that has invalid input, and the value is a human-readable error message.  If no input errors are
    found, then the callable should return an empty dictionary.  As usual, the callable can request any standard dependencies configured
    in the dependency injection container or proivded by input_output.get_context_for_callables.

    Note that most endpoints (such as Create and Update) explicitly require input.  As a result, if a request comes in without input
    from the end user, it will be rejected before calling your input validator.  In these cases you can depend on request_data always
    being a dictionary.  The Callable endpoint, however, only requires input if `writeable_column_names` is set.  If it's not set,
    and the end-user doesn't provide a request body, then request_data will be None.

    ```
    import clearskies

    def check_input(request_data):
        if not request_data:
            return {}
        if request_data.get("name"):
            return {"name":"This is a privacy-preserving system, so please don't tell us your name"}
        return {}

    send_user = clearskies.endpoints.Callable(
        lambda request_data: request_data,
        request_methods=["GET", "POST"],
        input_validation_callable=check_input,
    )

    wsgi = clearskies.contexts.WsgiRef(send_user)
    wsgi()
    ```

    And when invoked:

    ```
    $ curl http://localhost:8080 -d '{"name":"sup"}' | jq
    {
        "status": "input_errors",
        "error": "",
        "data": [],
        "pagination": {},
        "input_errors": {
            "name": "This is a privacy-preserving system, so please don't tell us your name"
        }
    }

    $ curl http://localhost:8080 -d '{"hello":"world"}' | jq
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

    """
    input_validation_callable = clearskies.configs.Callable(default=None)

    """
    A dictionary with columns that should override columns in the model.

    This is typically used to change column definitions on specific endpoints to adjust behavior: for intstance a model might use a `created_by_*`
    column to auto-populate some data, but an admin endpoint may need to override that behavior so the user can set it directly.

    This should be a dictionary with the column name as a key and the column itself as the value.  Note that you cannot use this to remove
    columns from the model.  In general, if you want a column not to be exposed through an endpoint, then all you have to do is remove
    that column from the list of writeable columns.

    ```
    import clearskies

    endpoint = clearskies.Endpoint(
        column_overrides = {
            "name": clearskies.columns.String(validators=clearskies.validators.Required()),
        }
    )
    ```
    """
    column_overrides = clearskies.configs.Columns(default={})

    """
    Used in conjunction with external_casing to change the casing of the key names in the outputted JSON of the endpoint.

    To use these, set internal_casing to the casing scheme used in your model, and then set external_casing to the casing
    scheme you want for your API endpoints.  clearskies will then automatically convert all output key names accordingly.
    Note that for callables, this only works when you return a model and set `readable_columns`.  If you set `writeable_columns`,
    it will also map the incoming data.

    The allowed casing schemas are:

     1. `snake_case`
     2. `camelCase`
     3. `TitleCase`

    By default internal_casing and external_casing are both set to 'snake_case', which means that no conversion happens.

    ```
    import clearskies
    import datetime

    class User(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        date_of_birth = clearskies.columns.Date()

    send_user = clearskies.endpoints.Callable(
        lambda users: users.create({"name":"Example","date_of_birth": datetime.datetime(2050, 1, 15)}),
        readable_column_names=["name", "date_of_birth"],
        internal_casing="snake_case",
        external_casing="TitleCase",
        model_class=User,
    )

    # because we're using name-based injection in our lambda callable (instead of type hinting) we have to explicitly
    # add the user model to the dependency injection container
    wsgi = clearskies.contexts.WsgiRef(send_user, classes=[User])
    wsgi()
    ```

    And then when called:

    ```
    $ curl http://localhost:8080  | jq
    {
        "Status": "Success",
        "Error": "",
        "Data": {
            "Name": "Example",
            "DateOfBirth": "2050-01-15"
        },
        "Pagination": {},
        "InputErrors": {}
    }
    ```
    """
    internal_casing = clearskies.configs.Select(['snake_case', 'camelCase', 'TitleCase'], default='snake_case')

    """
    Used in conjunction with internal_casing to change the casing of the key names in the outputted JSON of the endpoint.

    See the docs for `internal_casing` for more details and usage examples.
    """
    external_casing = clearskies.configs.Select(['snake_case', 'camelCase', 'TitleCase'], default='snake_case')

    """
    Configure standard security headers to be sent along in the response from this endpoint.

    Note that, with CORS, you generally only have to specify the origin.  The routing system will automatically add
    in the appropriate HTTP verbs, and the authorization classes will add in the appropriate headers.

    ```
    import clearskies

    hello_world = clearskies.endpoints.Callable(
        lambda: {"hello": "world"},
        request_methods=["PATCH", "POST"],
        authentication=clearskies.authentication.SecretBearer(environment_key="MY_SECRET"),
        security_headers=[
            clearskies.security_headers.Hsts(),
            clearskies.security_headers.Cors(origin="https://example.com"),
        ],
    )

    wsgi = clearskies.contexts.WsgiRef(hello_world)
    wsgi()
    ```

    And then execute the options endpoint to see all the security headers:

    ```
    $ curl -v http://localhost:8080 -X OPTIONS
    * Host localhost:8080 was resolved.
    < HTTP/1.0 200 Ok
    < Server: WSGIServer/0.2 CPython/3.11.6
    < ACCESS-CONTROL-ALLOW-METHODS: PATCH, POST
    < ACCESS-CONTROL-ALLOW-HEADERS: Authorization
    < ACCESS-CONTROL-MAX-AGE: 5
    < ACCESS-CONTROL-ALLOW-ORIGIN: https://example.com
    < STRICT-TRANSPORT-SECURITY: max-age=31536000 ;
    < CONTENT-TYPE: application/json; charset=UTF-8
    < Content-Length: 0
    <
    * Closing connection
    ```

    """
    security_headers = clearskies.configs.SecurityHeaders(default=[])

    """
    A description for this endpoint.  This is added to any auto-documentation
    """
    description = clearskies.configs.String(default="")

    cors_header: SecurityHeader = None  # type: ignore
    has_cors: bool = False
    _model: clearskies.model.Model = None
    _columns: dict[str, clearskies.column.Column] = None
    _readable_columns: dict[str, clearskies.column.Column] = None
    _writeable_columns: dict[str, clearskies.column.Column] = None
    _searchable_columns: dict[str, clearskies.column.Column] = None
    _as_json_map: dict[str, clearskies.column.Column] = None # type: ignore

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        url: str = "",
        request_methods: list[str] = ["GET"],
        response_headers: list[str | Callable[..., list[str]]] = [],
        output_map: Callable[..., dict[str, Any]] | None = None,
        column_overrides: dict[str, Column] = {},
        internal_casing: str = "snake_case",
        external_casing: str = "snake_case",
        security_headers: list[SecurityHeader] = [],
        description: str = "",
        authentication: Authentication = Public(),
        authorization: Authorization = Authorization(),
    ):
        self.finalize_and_validate_configuration()
        for security_header in self.security_headers:
            if not security_header.is_cors:
                continue
            self.cors_header = security_header
            self.has_cors = True
            break

    @property
    def model(self) -> Model:
        if self._model is None:
            self._model = self.di.build(self.model_class)
        return self._model

    @property
    def columns(self) -> dict[str, Column]:
        if self._columns is None:
            self._columns = self.model.get_columns()
        return self._columns

    @property
    def readable_columns(self) -> dict[str, Column]:
        if self._readable_columns is None:
            self._readable_columns = {name: self.columns[name] for name in self.readable_column_names}
        return self._readable_columns

    @property
    def writeable_columns(self) -> dict[str, Column]:
        if self._writeable_columns is None:
            self._writeable_columns = {name: self.columns[name] for name in self.writeable_column_names}
        return self._writeable_columns

    @property
    def sortable_columns(self) -> dict[str, Column]:
        if self._sortable_columns is None:
            self._sortable_columns = {name: self._columns[name] for name in self.sortable_column_names}
        return self._sortable_columns


    def top_level_authentication_and_authorization(self, input_output: InputOutput) -> None:
        """
        Handle authentication and authorization for this endpoint.

        In the event of an AuthN/AuthZ issue, raise an exception.  Otherwise, return None
        """
        if not self.authentication:
            return
        try:
            if not self.authentication.authenticate(input_output):
                raise exceptions.Authentication("Not Authenticated")
        except exceptions.ClientError as client_error:
            raise exceptions.Authentication(str(client_error))
        if self.authorization:
            try:
                if not self.authorization.gate(input_output.authorization_data, input_output):
                    raise exceptions.Authorization("Not Authorized")
            except exceptions.ClientError as client_error:
                raise exception.Authorization(str(client_error))

    def __call__(self, input_output: InputOutput, route_standalone=True) -> Any:
        """
        Execute the endpoint!

        This function mostly just checks AuthN/AuthZ and then passes along control to the handle method.
        It also checks for all the appropriate exceptions from clearskies.exceptions and turns those into the
        expected response.  As a result, when building a new endpoint, you normally modify the handle method
        rather than this one.
        """

        # these two configs can have arbitrary classes attached, which may use injectable properties.  Because they are
        # hiding in configs, the system for automatically discovering these won't work, so we have to manually check them.
        # We can't do this in the constructor because self.di hasn't been populated yet, and we can't do this in
        # our own injectable_properties class method because we need to operate at the instance level
        for config_name in ["authentication", "authorization"]:
            config = getattr(self, config_name)
            if config and hasattr(config, "injectable_properties"):
                config.injectable_properties(self.di)

        # If we have been attached directly to a context then we get to do some routing ourselves.
        if route_standalone:
            request_method = input_output.get_request_method().upper()
            if request_method == "OPTIONS":
                return self.cors(input_output)
            if request_method not in self.request_methods:
                return self.error(input_output, "Not Found", 404)
            expected_url = self.url.strip('/')
            incoming_url = input_output.get_full_path().strip('/')
            if expected_url or incoming_url:
                matches, routing_data = routing.match_route(expected_url, incoming_url, allow_partial=False)
                if not matches:
                    return self.error(input_output, "Not Found", 404)
                input_output.routing_data = routing_data

        self.di.add_binding("input_output", input_output)
        try:
            self.top_level_authentication_and_authorization(input_output)
        except exceptions.Authentication as auth_error:
            return self.error(input_output, str(auth_error), 401)
        except exceptions.Authorization as auth_error:
            return self.error(input_output, str(auth_error), 403)
        except exceptions.NotFound as auth_error:
            return self.error(input_output, str(auth_error), 404)
        except exceptions.MovedPermanently as redirect:
            return self.redirect(input_output, str(redirect), 302)
        except exceptions.MovedTemporarily as redirect:
            return self.redirect(input_output, str(redirect), 307)

        try:
            response = self.handle(input_output)
        except exceptions.ClientError as client_error:
            return self.error(input_output, str(client_error), 400)
        except exceptions.InputErrors as input_errors:
            return self.input_errors(input_output, input_errors.errors)
        except exceptions.Authentication as auth_error:
            return self.error(input_output, str(auth_error), 401)
        except exceptions.Authorization as auth_error:
            return self.error(input_output, str(auth_error), 403)
        except exceptions.NotFound as auth_error:
            return self.error(input_output, str(auth_error), 404)
        except exceptions.MovedPermanently as redirect:
            return self.redirect(input_output, str(redirect), 302)
        except exceptions.MovedTemporarily as redirect:
            return self.redirect(input_output, str(redirect), 307)

        return response

    def input_errors(self, input_output: InputOutput, errors: dict[str, str], status_code: int=200) -> Any:
        """
        Return input errors to the client.
        """
        return self.respond_json(input_output, {"status": "input_errors", "input_errors": errors}, status_code)

    def error(self, input_output: InputOutput, message: str, status_code: int) -> Any:
        """
        Return a client-side error (e.g. 400)
        """
        return self.respond_json(input_output, {"status": "client_error", "error": message}, status_code)

    def redirect(self, input_output: InputOutput, location: str, status_code: int) -> Any:
        """
        Return a redirect.
        """
        input_output.response_headers.add("content-type", "text/html")
        input_output.response_headers.add("location", location)
        return self.respond('<meta http-equiv="refresh" content="0; url=' + urllib.parse.quote(location) + '">Redirecting', status_code)

    def success(self, input_output: InputOutput, data: dict[str, Any], number_results: int | None=None, limit: int | None=None, next_page: Any=None) -> Any:
        """
        Return a successful response.
        """
        response_data = {"status": "success", "data": data, "pagination": {}}

        if number_results is not None:
            for value in [number_results, limit]:
                if value is not None and type(value) != int:
                    raise ValueError("number_results and limit must all be integers")

            response_data["pagination"] = {
                "number_results": number_results,
                "limit": limit,
                "next_page": next_page,
            }

        return self.respond_json(input_output, response_data, 200)

    def respond_json(self, input_output: InputOutput, response_data: dict[str, Any], status_code: int) -> Any:
        if "content-type" not in input_output.response_headers:
            input_output.response_headers.add("content-type", "application/json")
        return self.respond(input_output, self.normalize_response(response_data), status_code)

    def respond(self, input_output: InputOutput, response: clearskies.typing.response, status_code: int) -> Any:
        if self.response_headers:
            if callable(self.response_headers):
                response_headers = self.di.call_function(self.response_headers, **input_output.get_context_for_callables())
            else:
                response_headers = self.response_headers

            for (index, response_header) in enumerate(response_headers):
                if not isinstance(response_header, str):
                    raise TypeError(f"Invalid response header in entry #{index+1}: the header should be a string, but I was given a type of '{header.__class__.__name__}' instead.")
                parts = response_header.split(":", 1)
                if len(parts) != 2:
                    raise ValueError(f"Invalid response header in entry #{index+1}: the header should be a string in the form of 'key: value' but the given header did not have a colon to separate key and value.")
                input_output.response_headers.add(parts[0], parts[1])
        for security_header in self.security_headers:
            security_header.set_headers_for_input_output(input_output)
        return input_output.respond(response, status_code)

    def normalize_response(self, response_data: dict[str, Any]) -> dict[str, Any]:
        if "status" not in response_data:
            raise ValueError("Huh, status got left out somehow")
        return {
            self.auto_case_internal_column_name("status"): self.auto_case_internal_column_name(response_data["status"]),
            self.auto_case_internal_column_name("error"): response_data.get("error", ""),
            self.auto_case_internal_column_name("data"): response_data.get("data", []),
            self.auto_case_internal_column_name("pagination"): self.normalize_pagination(response_data.get("pagination", {})),
            self.auto_case_internal_column_name("input_errors"): response_data.get("input_errors", {}),
        }

    def normalize_pagination(self, pagination: dict[str, Any]) -> dict[str, Any]:
        # pagination isn't always relevant so if it is completely empty then leave it that way
        if not pagination:
            return pagination
        return {
            self.auto_case_internal_column_name("number_results"): pagination.get("number_results", 0),
            self.auto_case_internal_column_name("limit"): pagination.get("limit", 0),
            self.auto_case_internal_column_name("next_page"): {
                self.auto_case_internal_column_name(key): value
                for (key, value) in pagination.get("next_page", {}).items()
            },
        }

    def auto_case_internal_column_name(self, column_name: str) -> str:
        if self.external_casing:
            return string.swap_casing(column_name, "snake_case", self.external_casing)
        return column_name

    def auto_case_column_name(self, column_name: str, internal_to_external: bool) -> str:
        if not self.internal_casing:
            return column_name
        if internal_to_external:
            return string.swap_casing(
                column_name,
                self.internal_casing,
                self.external_casing,
            )
        return string.swap_casing(
            column_name,
            self.external_casing,
            self.internal_casing,
        )

    def cors(self, input_output: InputOutput):
        """
        Handles a CORS request
        """
        if not self.cors_header:
            return self.respond(input_output, "not found", 404)
        if self.authentication:
            self.authentication.set_headers_for_cors(self.cors)
        cors.set_headers_for_input_output(input_output)
        return self.respond(input_output, "", 200)

    def model_as_json(self, model: clearskies.model.Model, input_output: clearskies.input_output.InputOutput) -> dict[str, Any]:
        if self.output_map:
            return self.di.call_function(self.output_map, model=model, **input_output.get_context_for_callables())

        if self._as_json_map is None:
            self._as_json_map = self._build_as_json_map(model)

        json = OrderedDict()
        for output_name, column in self._as_json_map.items():
            column_data = column.to_json(model)
            if len(column_data) == 1:
                json[output_name] = list(column_data.values())[0]
            else:
                for key, value in column_data.items():
                    json[self.auto_case_column_name(key, True)] = value
        return json

    def _build_as_json_map(self, model: clearskies.model.Model) -> dict[str, clearskies.column.Column]:
        conversion_map = {}
        for column in self.readable_columns.values():
            conversion_map[self.auto_case_column_name(column.name, True)] = column
        return conversion_map

    def validate_input_against_schema(self, request_data: dict[str, Any], input_output: InputOutput, schema: Schema) -> None:
        if not self.writeable_column_names:
            raise ValueError(f"I was asked to validate input against a schema, but no writeable columns are defined, so I can't :(  This is probably a bug in the endpoint class - {self.__class__.__name__}.")
        request_data = self.map_request_data_external_to_internal(request_data)
        self.find_input_errors(request_data, input_output, schema)

    def map_request_data_external_to_internal(self, request_data, required=True):
        # we have to map from internal names to external names, because case mapping
        # isn't always one-to-one, so we want to do it exactly the same way that the documentation
        # is built.
        key_map = {self.auto_case_column_name(key, True): key for key in self.writeable_column_names}

        # and make sure we don't drop any data along the way, because the input validation
        # needs to return an error for unexpected data.
        return {key_map.get(key, key): value for (key, value) in request_data.items()}

    def find_input_errors(self, request_data: dict[str, Any], input_output: InputOutput, schema: Schema) -> None:
        input_errors = {}
        columns = schema.get_columns()
        model = self.di.build(schema)
        for column_name in self.writeable_column_names:
            column = columns[column_name]
            input_errors = {
                **input_errors,
                **column.input_errors(model, request_data),
            }
        input_errors = {
            **input_errors,
            **self.find_input_errors_from_callable(request_data, input_output),
        }
        for extra_column_name in set(request_data.keys()) - set(self.writeable_column_names):
            external_column_name = self.auto_case_column_name(extra_column_name, False)
            input_errors[external_column_name] = f"Input column {external_column_name} is not an allowed input column."
        if input_errors:
            raise exceptions.InputErrors(input_errors)

    def find_input_errors_from_callable(self, request_data: dict[str, Any], input_output: InputOutput) -> dict[str, str]:
        if not self.input_validation_callable:
            return {}

        more_input_errors = self.di.call_function(
            self.input_validation_callable,
            **input_output.get_context_for_callables()
        )
        if not isinstance(more_input_errors, dict):
            raise ValueError(
                "The input error callable did not return a dictionary as required"
            )
        return more_input_errors

    def cors(self, input_output: InputOutput):
        from clearskies.security_headers.cors import Cors
        cors_header = self.cors_header if self.has_cors else Cors()
        for method in self.request_methods:
            cors_header.add_method(method)
        if self.authentication:
            self.authentication.set_headers_for_cors(cors_header)
        cors_header.set_headers_for_input_output(input_output)
        for security_header in self.security_headers:
            if security_header.is_cors:
                continue
            security_header.set_headers_for_input_output(input_output)
        return input_output.respond("", 200)

    def documentation(self) -> list[Request]:
        return []

    def documentation_components(self) -> dict[str, Any]:
        return {
            "models": self.documentation_models(),
            "securitySchemes": self.documentation_security_schemes(),
        }

    def documentation_security_schemes(self) -> dict[str, Any]:
        if not self.authentication or not self.authentication.documentation_security_scheme_name():
            return {}

        return {
            authentication.documentation_security_scheme_name(): authentication.documentation_security_scheme(),
        }

    def documentation_models(self) -> dict[str, schema.Schema]:
        return {}

    def documentation_pagination_response(self, include_pagination=True) -> schema.Schema:
        if not include_pagination:
            return schema.Object(self.auto_case_internal_column_name("pagination"), [], value={})
        model = self.di.build(self.model_class)
        return schema.Object(
            self.auto_case_internal_column_name("pagination"),
            [
                schema.Integer(self.auto_case_internal_column_name("number_results"), example=10),
                schema.Integer(self.auto_case_internal_column_name("limit"), example=100),
                schema.Object(
                    self.auto_case_internal_column_name("next_page"),
                    model.documentation_pagination_next_page_response(self.auto_case_internal_column_name),
                    model.documentation_pagination_next_page_example(self.auto_case_internal_column_name),
                ),
            ],
        )

    def documentation_success_response(self, data_schema: schema.Object, description: str="", include_pagination: bool=False) -> Response:
        return Response(
            200,
            schema.Object(
                "body",
                [
                    schema.String(self.auto_case_internal_column_name("status"), value="success"),
                    data_schema,
                    self.documentation_pagination_response(include_pagination=include_pagination),
                    schema.String(self.auto_case_internal_column_name("error"), value=""),
                    schema.Object(self.auto_case_internal_column_name("input_errors"), [], value={}),
                ],
            ),
            description=description,
        )

    def documentation_generic_error_response(self, description="Invalid Call", status=400) -> Response:
        return Response(
            status,
            schema.Object(
                "body",
                [
                    schema.String(self.auto_case_internal_column_name("status"), value="error"),
                    schema.Object(self.auto_case_internal_column_name("data"), [], value={}),
                    self.documentation_pagination_response(include_pagination=False),
                    schema.String(self.auto_case_internal_column_name("error"), example="User readable error message"),
                    schema.Object(self.auto_case_internal_column_name("input_errors"), [], value={}),
                ],
            ),
            description=description,
        )

    def documentation_input_error_response(self, description="Invalid client-side input") -> Response:
        email_example = self.auto_case_internal_column_name("email")
        return Response(
            200,
            schema.Object(
                "body",
                [
                    schema.String(self.auto_case_internal_column_name("status"), value="input_errors"),
                    schema.Object(self.auto_case_internal_column_name("data"), [], value={}),
                    self.documentation_pagination_response(include_pagination=False),
                    schema.String(self.auto_case_internal_column_name("error"), value=""),
                    schema.Object(
                        self.auto_case_internal_column_name("input_errors"),
                        [schema.String("[COLUMN_NAME]", example="User friendly error message")],
                        example={email_example: f"{email_example} was not a valid email address"},
                    ),
                ],
            ),
            description=description,
        )

    def documentation_access_denied_response(self) -> Response:
        return self.documentation_generic_error_response(description="Access Denied", status=401)

    def documentation_unauthorized_response(self) -> Response:
        return self.documentation_generic_error_response(description="Unauthorized", status=403)

    def documentation_not_found(self) -> Response:
        return self.documentation_generic_error_response(description="Not Found", status=404)

    def documentation_request_security(self):
        authentication = self.authentication
        name = authentication.documentation_security_scheme_name()
        return [{name: []}] if name else []

    def documentation_data_schema(self, schema: Schema=None, column_names: list[str] = []) -> list[Schema]:
        if schema is None:
            schema = self.model_class
        if column_names is None and self.readable_column_names:
            readable_column_names = self.readable_column_names
        properties = []

        columns = schema.get_columns()
        for column_name in readable_column_names:
            column = columns[readable_column_names]
            column_doc = column.documentation()
            if type(column_doc) != list:
                column_doc = [column_doc]
            for doc in column_doc:
                doc.name = self.auto_case_internal_column_name(doc.name)
                properties.append(doc)

        return properties

    def standard_json_request_parameters(self, schema: Schema=None, column_names: list[str] = []) -> list[Parameter]:
        if not column_names:
            if not self.writeable_column_names:
                return []
            column_names = self.writeable_column_names

        if not schema:
            if not self.model_class:
                return []
            schema = self.model_class

        model_name = string.camel_case_to_snake_case(schema.__name__)
        columns = schema.get_columns()
        return [
            autodoc.request.JSONBody(
                columns[column_name].documentation(name=self.auto_case_column_name(column_name, True)),
                description=f"Set '{column.name}' for the {model_name}",
                required=columns[column_name].is_required,
            )
            for column_name in writeable_column_names
        ]

    def standard_url_request_parameters(self) -> list[Parameter]:
        parameter_names = routing.extract_url_parameter_name_map(self.url.strip('/'))
        return [
            autodoc.request.URLPath(
                autodoc.schema.String(parameter_name),
                description=f"The {parameter_name}.",
                required=True,
            )
            for parameter_name in parameter_names.keys()
        ]

