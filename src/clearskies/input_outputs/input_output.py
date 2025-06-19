import json
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import parse_qs

import clearskies.configurable
import clearskies.typing
from clearskies.configs import AnyDict, StringDict
from clearskies.exceptions import ClientError

from .headers import Headers


class InputOutput(ABC, clearskies.configurable.Configurable):
    """Manage the request and response to the client."""

    response_headers: Headers = None  # type: ignore
    request_headers: Headers = None  # type: ignore
    query_parameters = clearskies.configs.AnyDict(default={})
    routing_data = clearskies.configs.StringDict(default={})
    authorization_data = clearskies.configs.AnyDict(default={})

    _body_as_json: dict[str, Any] | list[Any] | None = {}
    _body_loaded_as_json = False

    def __init__(self):
        self.response_headers = Headers()
        self.request_headers = Headers(self.get_request_headers())
        self.query_parameters = {key: val[0] for (key, val) in parse_qs(self.get_query_string()).items()}
        self.authorization_data = {}
        self.routing_data = {}
        self.finalize_and_validate_configuration()

    @abstractmethod
    def respond(self, body: clearskies.typing.response, status_code: int = 200) -> Any:
        """
        Pass along a response to the client.

        Accepts a string, bytes, dictionary, or list.  If a content type has not been set then it will automatically
        be set to application/json
        """
        pass

    @abstractmethod
    def get_body(self) -> str:
        """Return the raw body set by the client."""
        pass

    @abstractmethod
    def has_body(self) -> bool:
        """Whether or not the request included a body."""
        pass

    @property
    def request_data(self) -> dict[str, Any] | list[Any] | None:
        """Return the data from the request body, assuming it is JSON."""
        if not self._body_loaded_as_json:
            self._body_loaded_as_json = True
            if not self.has_body():
                self._body_as_json = None
            else:
                try:
                    self._body_as_json = json.loads(self.get_body())
                except json.JSONDecodeError:
                    self._body_as_json = None
        return self._body_as_json

    @abstractmethod
    def get_request_method(self) -> str:
        """Return the request method set by the client."""
        pass

    @abstractmethod
    def get_script_name(self) -> str:
        """Return the script name, e.g. the path requested."""
        pass

    @abstractmethod
    def get_path_info(self) -> str:
        """Return the path info for the request."""
        pass

    @abstractmethod
    def get_query_string(self) -> str:
        """Return the full query string for the request (everything after the first question mark in the document URL)."""
        pass

    @abstractmethod
    def get_client_ip(self):
        pass

    @abstractmethod
    def get_request_headers(self) -> dict[str, str]:
        pass

    def get_full_path(self) -> str:
        """Return the full path requested by the client."""
        path_info = self.get_path_info()
        script_name = self.get_script_name()
        if not path_info or path_info[0] != "/":
            path_info = f"/{path_info}"
        return f"{path_info}{script_name}".replace("//", "/")

    def context_specifics(self):
        return {}

    def get_context_for_callables(self) -> dict[str, Any]:
        """
        Return a dictionary with various important parts of the request that are passed along to user-defined functions.

        It's common to make various aspects of an incoming request available to user-defined functions that are
        attached to clearskies hooks everywhere.  This function centralizes the definition of what aspects of
        the reequest shouuld be passed along to callables in this case.  When this is in use it typically
        looks like this:

        di.call_function(some_function, **input_output.get_context_for_callables())

        And this function returns a dictionary with the following values:

        | Key                | Type                             | Ref                             | Value                                                                           |
        |--------------------|----------------------------------|---------------------------------|---------------------------------------------------------------------------------|
        | routing_data       | dict[str, str]                   | input_output.routing_data       | A dictionary of data extracted from URL path parameters.                        |
        | authorization_data | dict[str, Any]                   | input_output.authorization_data | A dictionary containing the authorization data set by the authentication method |
        | request_data       | dict[str, Any] | None            | input_output.request_data       | The data sent along with the request (assuming a JSON request body)             |
        | query_parameters   | dict[str, Any]                   | input_output.query_parameters   | The query parameters                                                            |
        | request_headers    | clearskies.input_outputs.Headers | input_output.request_headers    | The request headers sent by the client                                          |
        | **routing_data     | string                           | **input_output.routing_data     | The routing data is unpacked so keys can be fetched directly                    |
        """
        return {
            **self.routing_data,
            **{
                "routing_data": self.routing_data,
                "authorization_data": self.authorization_data,
                "request_data": self.request_data,
                "request_headers": self.request_headers,
                "query_parameters": self.query_parameters,
            },
        }
