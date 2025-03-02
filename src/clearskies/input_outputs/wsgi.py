from .input_output import InputOutput
import urllib, urllib.parse
import json


class Wsgi(InputOutput):
    _environment = None
    _start_response = None
    _request_headers = None
    _cached_body = None

    def __init__(self, environment, start_response):
        self._environment = environment
        self._start_response = start_response
        self._request_headers = {}
        for key, value in self._environment.items():
            if key.upper()[0:5] == "HTTP_":
                self._request_headers[key[5:].lower()] = value
        super().__init__()

    def _from_environment(self, key):
        return self._environment[key] if key in self._environment else ""

    def respond(self, body, status_code=200):
        if "content-type" not in self.response_headers:
            self.response_headers.content_type = "application/json; charset=UTF-8"

        self._start_response(f"{status_code} Ok", [header for header in self.response_headers.items()])
        if type(body) == bytes:
            final_body = body
        elif type(body) == str:
            final_body = body.encode("utf-8")
        else:
            final_body = json.dumps(body).encode("utf-8")
        return [final_body]

    def has_body(self):
        return bool(self._from_environment('CONTENT_LENGTH'))

    def get_body(self):
        if self._cached_body is None:
            self._cached_body = self._from_environment("wsgi.input").read(int(self._from_environment('CONTENT_LENGTH'))).decode("utf-8") if self._from_environment('CONTENT_LENGTH') else ""
        return self._cached_body

    def get_request_method(self):
        return self._from_environment("REQUEST_METHOD").upper()

    def get_script_name(self):
        return self._from_environment("SCRIPT_NAME")

    def get_path_info(self):
        return self._from_environment("PATH_INFO")

    def get_query_string(self):
        return self._from_environment("QUERY_STRING")

    def get_content_type(self):
        return self._from_environment("CONTENT_TYPE")

    def get_protocol(self):
        return self._from_environment("wsgi.url_scheme").lower()

    def context_specifics(self):
        return {"wsgi_environment": self._environment}

    def get_client_ip(self):
        return self._environment.get("REMOTE_ADDR")

    def get_request_headers(self):
        return self._request_headers
