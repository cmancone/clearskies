from .input_output import InputOutput
import urllib, urllib.parse
import json


class WSGI(InputOutput):
    _environment = None
    _start_response = None
    _request_headers = None
    _cached_body = None
    _query_parameters = None

    def __init__(self, environment, start_response):
        self._environment = environment
        self._start_response = start_response
        self._request_headers = {}
        for (key, value) in self._environment.items():
            if key.upper()[0:5] == 'HTTP_':
                self._request_headers[key[5:].lower()] = value

    def _from_environment(self, key):
        return self._environment[key] if key in self._environment else ''

    def respond(self, body, status_code):
        if not self.has_header('content-type'):
            self.set_header('content-type', 'application/json; charset=UTF-8')

        self._start_response(
            f'{status_code} Ok',
            [header for header in self._response_headers.items()]
        )
        if type(body) == bytes:
            final_body = body
        elif type(body) == str:
            final_body = body.encode('utf-8')
        else:
            final_body = json.dumps(body).encode('utf-8')
        return [final_body]

    def has_body(self):
        return bool(self.get_body())

    def get_body(self):
        if self._cached_body is None:
            self._cached_body = self._from_environment('wsgi.input').read().decode('utf-8')
        return self._cached_body

    def get_request_method(self):
        return self._from_environment('REQUEST_METHOD').upper()

    def get_script_name(self):
        return self._from_environment('SCRIPT_NAME')

    def get_path_info(self):
        return self._from_environment('PATH_INFO')

    def get_query_string(self):
        return self._from_environment('QUERY_STRING')

    def get_content_type(self):
        return self._from_environment('CONTENT_TYPE')

    def get_protocol(self):
        return self._from_environment('wsgi.url_scheme').lower()

    def has_request_header(self, header_name):
        return header_name.lower() in self._request_headers

    def get_request_header(self, header_name, silent=False):
        if not header_name.lower() in self._request_headers:
            if not silent:
                raise KeyError(f"HTTP header '{header_name}' was not found in request")
            return ''
        return self._request_headers[header_name.lower()]

    def _parse_query_parameters(self):
        if self._query_parameters is None:
            self._query_parameters = urllib.parse.parse_qs(self.get_query_string())

    def get_query_parameter(self, key):
        self._parse_query_parameters()
        return self._query_parameters[key] if key in self._query_parameters else []

    def get_query_parameters(self):
        self._parse_query_parameters()
        return self._query_parameters
