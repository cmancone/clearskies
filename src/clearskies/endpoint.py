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
from clearskies.functional import string

if TYPE_CHECKING:
    from clearskies import Column, Model, SecurityHeader
    from clearskies.input_output import InputOutput

class Endpoint(clearskies.configurable.Configurable, clearskies.di.InjectableProperties):
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
    This should be given a list of either strings or callables that return strings.  In the case of callables,
    they should return a list of strings that represent the header key/value pairs, and can accept any of the
    standard dependencies or context-specific values:

    ```
    import clearskies

    def custom_headers(request_data):
        some_value = "yes" if request_data.get("stuff") else "no"
        return [f"x-custom: {some_value}"]

    endpoint = clearskies.endpoint(
        response_headers=["content-type: application/custom", custom_headers],
    )
    ```
    """
    response_headers = clearskies.configs.StringListOrCallable(default=[])

    """
    The URL for this endpoint.
    """
    url = clearskies.configs.String(default="")

    """
    The allowed request methods for this endpoint.
    """
    request_methods = clearskies.configs.SelectList(allowed_values=["GET", "POST", "PUT", "DELETE", "PATCH"], default=["GET"])

    """
    The authentication for this endpoint (default is public)
    """
    authentication = clearskies.configs.Authentication(default=Public())

    """
    The authorization rules for this endpoint
    """
    authorization = clearskies.configs.Authorization(default=Authorization())

    """
    An override of the default model-to-json mapping for endpoints that auto-convert models to json.  The model being converted is always injected
    via an argument named "model".

    ```
    def convert_model_to_json(model, utcnow):
        return {"id": model.some_other_column, "normalized_name": model.name.lower().replace(" ", "-"), "response_at": utcnow.isoformat()}

    endpoint = clearskies.Endpoint(
        output_map = convert_model_to_json,
    )
    ```
    """
    output_map = clearskies.configs.Callable()

    """
    The model class that we will be passing back to the user.
    """
    model_class = clearskies.configs.ModelClass()

    """
    Columns from the model class that should be returned to the client.
    """
    readable_column_names = clearskies.configs.ReadableModelColumns("model_class")

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

    By default internal_casing and external_casing are both set to 'snake_case', which means that no conversion happens.
    """
    internal_casing = clearskies.configs.Select(['snake_case', 'camelCase', 'TitleCase'], default='snake_case')

    """
    Used in conjunction with internal_casing to change the casing of the key names in the outputted JSON of the endpoint.

    To use these, set internal_casing to the casing scheme used in your model, and then set external_casing to the casing
    scheme you want for your API endpoints.  clearskies will then automatically convert all output key names accordingly.

    By default internal_casing and external_casing are both set to 'snake_case', which means that no conversion happens.
    """
    external_casing = clearskies.configs.Select(['snake_case', 'camelCase', 'TitleCase'], default='snake_case')

    """
    Configure standard security headers to be sent along in the response from this endpoint.

    ```
    import clearskies

    endpoint = clearskies.Endpoint(
        security_headers=[
            clearskies.security_headers.Hsts(),
            clearskies.security_headers.Cors(origin="https://example.com"),
        ],
    )
    ```
    """
    security_headers = clearskies.configs.SecurityHeaders(default=[])

    """
    A description for this endpoint.  This is added to any auto-documentation
    """
    description = clearskies.configs.String()

    cors_header: SecurityHeader = None  # type: ignore
    has_cors: bool = False
    _model: clearskies.model.Model = None
    _columns: dict[str, clearskies.column.Column] = None
    _readable_columns: dict[str, clearskies.column.Column] = None
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
        for security_header in security_headers:
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

    def __call__(self, input_output: InputOutput) -> Any:
        """
        Execute the endpoint!

        This function mostly just checks AuthN/AuthZ and then passes along control to the handle method.
        It also checks for all the appropriate exceptions from clearskies.exceptions and turns those into the
        expected response.  As a result, when building a new endpoint, you normally modify the handle method
        rather than this one.
        """
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
        input_output.response_headers.add("content-type", "application/json")
        return input_output.respond(self.normalize_response(response_data), status_code)

    def respond(self, input_output: InputOutput, response: clearskies.typing.response, status_code: int) -> Any:
        if self.response_headers:
            for (index, response_header) in enumerate(self.response_headers):
                # each entry is either a string or a callable that returns a list of strings.  Since the callable returns a list,
                # we end up with another loop
                if callable(response_header):
                    more_response_headers = self.di.call_function(response_header, **input_output.get_context_for_callables())
                else:
                    more_response_headers = [response_header]
                for header in more_response_headers:
                    if not isinstance(header, str):
                        raise TypeError(f"Invalid response header in entry #{index+1}: the header should be a string, but I was given a type of '{header.__class__.__name__}' instead.")
                    parts = header.split(":", 1)
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
            return self.di.call_function(output_map, model=model, **input_output.get_context_for_callables())

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
        conversion_map[self.auto_case_column_name(model.id_column_name, True)] = model.get_columns()[model.id_column_name]

        for column in self.readable_columns.values():
            conversion_map[self.auto_case_column_name(column.name, True)] = column
        return conversion_map

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

    def documentation_data_schema(self) -> list[Schema]:
        id_column_name = self.model_class.id_column_name
        properties = [
            self.columns[id_column_name].documentation(name=self.auto_case_column_name(id_column_name, True))
        ]

        for column in self.readable_columns:
            column_doc = column.documentation()
            if type(column_doc) != list:
                column_doc = [column_doc]
            for doc in column_doc:
                doc.name = self.auto_case_internal_column_name(doc.name)
                properties.append(doc)

        return properties

    def documentation_id_url_parameter(self) -> Parameter:
        return autodoc.request.URLPath(
            self.columns[self.model_class.id_column_name].documentation(),
            description="The id of the record to fetch",
            required=True,
        )
