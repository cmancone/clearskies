from ..input_output import InputOutput
import urllib


class WSGI(InputOutput):
    self._environment = None
    self._start_response = None
    self._request_headers = None
    self._cached_body = None
    self._query_parameters = None

    def __init__(self, environment, start_response):
        self._environment = environment
        self._start_response = start_response
        self._request_headers = {}
        for (key, value) in self._environment.items():
            if key[0:5] === 'HTTP_':
                self._request_headers[key[5:].lower()] = value

    def _from_environment(self, key):
        return _environment[key] if key in self._environment else ''

    def respond(self, body, status_code):
        if not self.has_header('content-type'):
            self.add_header('content-type', 'application/json; charset=UTF-8')

        headers = []
        if self._response_headers:
            headers = list(self._response_headers)

        self._start_response(f'{status_code} Ok', headers)
        return [body] if type(body) == bytes else [body.encode('utf-8')]

    def has_body(self):
        return (bool) self.get_body()

    def get_body(self):
        if self._cached_body is None:
            self._cached_body = environ['wsgi.input'].read().decode('utf-8')
        return self._cached_body

    def get_request_method(self):
        return self._from_environment('REQUEST_METHOD')

    def get_path_info(self):
        return self._from_environment('PATH_INFO')

    def get_query_string(self):
        return self._from_environment('QUERY_STRING')

    def get_content_type(self):
        return self._from_environment('CONTENT_TYPE')

    def get_protocol(self):
        return self._from_environment('wsgi.url_scheme')

    def has_request_header(self, header_name):
        return header_name.lower() in self._request_headers

    def get_request_header(self, key, silent=False):
        if not header_name.lower() in self._request_headers:
            if not silent:
                raise KeyError(f"HTTP header '{key}' was not found in request")
            return ''
        return self._request_headers[header_name.lower()]

    def _parse_query_parameters(self):
        if self._query_parameters is None:
            self._query_parameters = urllib.parse.parse_qs(self.query_string())

    def get_query_parameter(self, key):
        self._parse_query_parameters()
        return self._query_parameters[key] if key in self._query_parameters else []

    def get_query_parameters(self):
        self._parse_query_parameters()
        return self._query_parameters
