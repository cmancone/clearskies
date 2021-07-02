from .input_output import InputOutput
import json
import base64
import urllib


class AWSLambdaAPIGateway(InputOutput):
    _event = None
    _context = None
    _request_headers = None
    _request_method = None
    _path = None
    _resource = None
    _query_parameters = None
    _path_parameters = None
    _cached_body = None
    _body_was_cached = False

    def __init__(self, event, context):
        self._event = event
        self._context = context
        self._request_method = event['httpMethod'].upper()
        self._path = event['path']
        self._resource = event['resource']
        self._query_parameters = event['queryStringParameters'] if event['queryStringParameters'] is not None else {}
        self._path_parameters = event['pathParameters']
        self._request_headers = {}
        for (key, value) in event['headers'].items():
            self._request_headers[key.lower()] = value

    def respond(self, body, status_code=200):
        if not self.has_header('content-type'):
            self.set_header('content-type', 'application/json; charset=UTF-8')

        if type(body) == bytes:
            final_body = body.decode('utf-8')
        elif type(body) == str:
            final_body = body
        else:
            final_body = json.dumps(body)

        return {
            "isBase64Encoded": False,
            "statusCode": status_code,
            "headers": self._response_headers,
            "body": final_body,
        }

    def has_body(self):
        return bool(self.get_body())

    def get_body(self):
        if not self._body_was_cached:
            self._cached_body = self._event['body']
            if self._cached_body is not None and self._event['isBase64Encoded']:
                self._cached_body = base64.decodebytes(self._cached_body.encode('utf-8')).decode('utf-8')
        return self._cached_body

    def get_request_method(self):
        return self._request_method

    def get_script_name(self):
        return ''

    def get_path_info(self):
        return self._path

    def get_query_string(self):
        return urllib.parse.urlencode(self._query_parameters)

    def get_content_type(self):
        return self.get_request_header('content-type', True)

    def get_protocol(self):
        return 'https'

    def has_request_header(self, header_name):
        return header_name.lower() in self._request_headers

    def get_request_header(self, header_name, silent=False):
        if not header_name.lower() in self._request_headers:
            if not silent:
                raise KeyError(f"HTTP header '{header_name}' was not found in request")
            return ''
        return self._request_headers[header_name.lower()]

    def get_query_parameter(self, key):
        return self._query_parameters[key] if key in self._query_parameters else []

    def get_query_parameters(self):
        return self._query_parameters
