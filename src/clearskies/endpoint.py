from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING

import clearskies.configurable
import clearskies.config
import clearskies.parameters_to_properties
import clearskies.configs

if TYPE_CHECKING:
    from clearskies import Column, SecurityHeader

class Endpoint(clearskies.configurable.Configurable, clearskies.di.InjectableProperties):
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

    # authentication = clearskies.configs.Authentication()

    # authorization = clearskies.configs.Authorization()

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
            "name": clearskies.columns.String(validators=clearskies.validators.Requird()),
        }
    )
    ```
    """
    column_overrides = clearksies.configs.Columns()

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

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        response_headers: list[str | Callable[..., list[str]] = [],
        output_map: Callable[..., dict[str, Any]],
        column_overrides: dict[str, Column] = {},
        id_column_name: str = "",
        internal_casing: str = "snake_case",
        external_casing: str = "snake_case",
        security_headers: list[SecurityHeader] = [],
    );
        self.finalize_and_validate_configuration()
