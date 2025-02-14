from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING
import urllib.parse

import clearskies.di
import clearskies.configurable
import clearskies.config
import clearskies.parameters_to_properties
import clearskies.configs
from clearskies import exceptions
from clearskies.authentication import Authentication, Authorization, Public

if TYPE_CHECKING:
    from clearskies import Column, SecurityHeader
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
    column_overrides = clearksies.configs.Columns(default={})

    """
    The name of the column to use when looking up records from routing parameters.

    By default, this is populated with the model.id_column_name
    """
    id_column_name = clearskies.configs.String()

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

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        response_headers: list[str | Callable[..., list[str]] = [],
        output_map: Callable[..., dict[str, Any]] | None = None,
        column_overrides: dict[str, Column] = {},
        id_column_name: str = "",
        internal_casing: str = "snake_case",
        external_casing: str = "snake_case",
        security_headers: list[SecurityHeader] = [],
        description: str = "",
        authentication: Authentication = Public(),
        authorization: Authorization = Authorization(),
    );
        self.finalize_and_validate_configuration()

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
            authorization_data = input_output.get_authorization_data()
            try:
                if not authorization.gate(authorization_data, input_output):
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
        except exceptions.InputError as input_error:
            return self.input_errors(input_output, input_error.errors)
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

    def input_errors(self, input_output: InputOutput, errors: dict[str, str], status_code: int=200):
        return self.respond(input_output, {"status": "input_errors", "input_errors": errors}, status_code)

    def error(self, input_output: InputOutput, message: str, status_code: int):
        return self.respond(input_output, {"status": "client_error", "error": message}, status_code)

    def redirect(self, input_output: InputOutput, location: str, status_code: int):
        input_output.set_headers("content-type: text/html")
        input_output.set_headers(f"location: {location}")
        return input_output.respond('<meta http-equiv="refresh" content="0; url=' + urllib.parse.quote(location) + '">Redirecting', status_code)

    def success(self, input_output: InputOutput, data: dict[str, Any], number_results: int | None=None, limit: int | None=None, next_page: Any=None):
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

        return self.respond(input_output, response_data, 200)

    def respond(self, input_output, response_data, status_code):
        response_headers = self.configuration("response_headers")
        if response_headers:
            input_output.set_headers(response_headers)
        for security_header in self.configuration("security_headers"):
            security_header.set_headers_for_input_output(input_output)
        return input_output.respond(self._normalize_response(response_data), status_code)
