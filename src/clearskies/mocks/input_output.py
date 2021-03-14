import json
from .. import input_outputs


class InputOutput(input_outputs.InputOutput):
    _body = None
    _request_method = None
    response = None

    def __init__(self, request_headers=None, body=None, request_method='GET'):
        self.set_request_method(request_method)
        self.set_body(body)
        self.set_request_headers(request_headers)

    def respond(self, body, status_code=200):
        self.response = {
            'body': body,
            'status_code': status_code,
            'headers': self._response_headers
        }
        return (body, status_code)

    def get_body(self):
        return self._body

    def has_body(self):
        return bool(self._body)

    def set_body(self, body):
        self._body = None
        if body:
            self._body = body if type(body) == str else json.dumps(body)

    def get_request_method(self):
        return self._request_method

    def set_request_method(self, request_method):
        self._request_method = request_method.upper()

    def set_request_headers(self, request_headers):
        self._request_headers = {}
        if request_headers is None:
            request_headers = {}
        for (key, value) in request_headers.items():
            self._request_headers[key.lower()] = value

    def get_path_info(self):
        return ''

    def get_query_string(self):
        return ''

    def get_content_type(self):
        return ''

    def get_protocol(self):
        return ''

    def has_request_header(self, header_name):
        return header_name.lower() in self._request_headers

    def get_request_header(self, header_name, silent=True):
        if not self.has_request_header(header_name):
            if not silent:
                raise ValueError(f"Request header '{header_name}' not found in request")
            return ''
        return self._request_headers[header_name.lower()]

    def get_query_parameter(self, key):
        return ''

    def get_query_parameters(self):
        return ''
