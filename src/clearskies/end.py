# type: ignore
from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from clearskies.input_output import InputOutput

from clearskies import exceptions
from clearskies.functional import string


class End(ABC):
    """
    DRY for endpoint and endpoint groups.

    This class is just here to hold some common functionality between Endpoints and EndpointGroups.
    The two classes have plenty of overlap but are different enough that I don't want either to inherit
    from the other.
    """

    def add_url_prefix(self, prefix: str) -> None:
        self.url = (prefix.rstrip("/") + "/" + self.url.lstrip("/")).lstrip("/")

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
        Execute the endpoint.

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

        response = self.populate_routing_data(input_output)
        if response:
            return response

        self.di.add_binding("input_output", input_output)

        # catch everything when we do an AuthN/AuthZ check because we allow custom-defined classes,
        # and this gives more flexibility (or possibly forgiveness) for how they raise exceptions.
        try:
            self.top_level_authentication_and_authorization(input_output)
        except exceptions.Authentication as auth_error:
            return self.error(input_output, str(auth_error), 401)
        except exceptions.Authorization as auth_error:
            return self.error(input_output, str(auth_error), 403)
        except exceptions.NotFound as not_found:
            return self.error(input_output, str(not_found), 404)
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

    def populate_routing_data(self, input_output: InputOutput) -> Any:
        raise NotImplementedError()

    def add_response_headers(self, input_output: InputOutput) -> None:
        if self.response_headers:
            if callable(self.response_headers):
                response_headers = self.di.call_function(
                    self.response_headers, **input_output.get_context_for_callables()
                )
            else:
                response_headers = self.response_headers

            for index, response_header in enumerate(response_headers):
                if not isinstance(response_header, str):
                    raise TypeError(
                        f"Invalid response header in entry #{index + 1}: the header should be a string, but I was given a type of '{header.__class__.__name__}' instead."
                    )
                parts = response_header.split(":", 1)
                if len(parts) != 2:
                    raise ValueError(
                        f"Invalid response header in entry #{index + 1}: the header should be a string in the form of 'key: value' but the given header did not have a colon to separate key and value."
                    )
                input_output.response_headers.add(parts[0], parts[1])
        for security_header in self.security_headers:
            security_header.set_headers_for_input_output(input_output)

    def respond(self, input_output: InputOutput, response: clearskies.typing.response, status_code: int) -> Any:
        self.add_response_headers(input_output)
        return input_output.respond(response, status_code)

    def respond_json(self, input_output: InputOutput, response_data: dict[str, Any], status_code: int) -> Any:
        if "content-type" not in input_output.response_headers:
            input_output.response_headers.add("content-type", "application/json")
        return self.respond(input_output, self.normalize_response(response_data), status_code)

    def normalize_response(self, response_data: dict[str, Any]) -> dict[str, Any]:
        if "status" not in response_data:
            raise ValueError("Huh, status got left out somehow")
        return {
            self.auto_case_internal_column_name("status"): self.auto_case_internal_column_name(response_data["status"]),
            self.auto_case_internal_column_name("error"): response_data.get("error", ""),
            self.auto_case_internal_column_name("data"): response_data.get("data", []),
            self.auto_case_internal_column_name("pagination"): self.normalize_pagination(
                response_data.get("pagination", {})
            ),
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
