from typing import Any

from clearskies.input_outputs.input_output import InputOutput

from .headers import Headers


class Programmatic(InputOutput):
    _body: str | dict[str, Any] | list[Any] = ""
    _request_method: str = ""
    _request_headers: dict[str, Any] = {}
    url: str = ""

    def __init__(
        self,
        url: str = "",
        request_method: str = "GET",
        body: str | dict[str, Any] | list[Any] = "",
        query_parameters: dict[str, Any] = {},
        request_headers: dict[str, str] = {},
    ):
        self.url = url
        self._request_headers = {**request_headers}
        self._body_loaded_as_json = True
        self._body_as_json = None
        self._request_method = request_method
        if body:
            self._body = body
            if isinstance(body, dict) or isinstance(body, list):
                self._body_as_json = body

        super().__init__()
        self.query_parameters = {**query_parameters}

    def respond(self, response, status_code=200):
        return (status_code, response, self.response_headers)

    def get_script_name(self):
        return self.url

    def get_path_info(self):
        return self.url

    def get_full_path(self):
        return self.url

    def get_request_method(self):
        return self._request_method

    def has_body(self):
        return bool(self._body)

    def get_body(self):
        if not self.has_body():
            return ""

        return self._body

    def context_specifics(self):
        return {}

    def get_client_ip(self):
        return "127.0.0.1"

    def get_query_string(self):
        return ""

    def get_request_headers(self):
        return self._request_headers
