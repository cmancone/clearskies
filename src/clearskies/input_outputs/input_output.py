from abc import ABC, abstractmethod
from collections import OrderedDict
from ..handlers.exceptions import ClientError
import json


class InputOutput(ABC):
    _response_headers = None
    _body_as_json = None
    _body_loaded_as_json = False
    _routing_data = None
    _authorization_data = None

    @abstractmethod
    def respond(self, body, status_code=200):
        pass

    def error(self, body):
        return self.respond(body, 400)

    def success(self, body):
        return self.respond(body)

    def configure(self):
        pass

    def has_header(self, key):
        if self._response_headers is None:
            return False
        return key.upper() in self._response_headers

    def set_header(self, key, value):
        if self._response_headers is None:
            self._response_headers = OrderedDict()
        self._response_headers[key.upper()] = value

    def clear_header(self, key):
        if self._response_headers is None:
            return
        if self.has_header(key):
            del self._response_headers[key.upper()]

    def clear_headers(self, key):
        self._response_headers = None

    def set_headers(self, headers):
        for key, value in headers.items():
            self.set_header(key, value)

    @abstractmethod
    def get_body(self):
        pass

    @abstractmethod
    def has_body(self):
        pass

    def routing_data(self):
        return self._routing_data if self._routing_data is not None else {}

    def set_routing_data(self, data):
        self._routing_data = data

    def add_routing_data(self, key, value=None):
        if self._routing_data is None:
            self._routing_data = {}
        if type(key) == dict:
            self._routing_data = {**self._routing_data, **key}
        else:
            self._routing_data[key] = value

    def request_data(self, required=True, allow_non_json_bodies=False):
        request_data = self.json_body(False, allow_non_json_bodies=allow_non_json_bodies)
        if not request_data:
            if self.has_body() and not allow_non_json_bodies:
                raise ClientError("Request body was not valid JSON")
            request_data = {}
        return request_data

    def json_body(self, required=True, allow_non_json_bodies=False):
        json = self._get_json_body()
        # if we get None then either the body was not JSON or was empty.
        # If it is required then we have an exception either way.  If it is not required
        # then we have an exception if a body was provided but it was not JSON.  We can check for this
        # if json is None and there is an actual request body.  If json is none, the body is empty,
        # and it was not required, then we can just return None
        if json is None:
            if required or (self.has_body() and not allow_non_json_bodies):
                raise ClientError("Request body was not valid JSON")
        return json

    def _get_json_body(self):
        if not self._body_loaded_as_json:
            if self.get_body() is None:
                self._body_as_json = None
            else:
                self._body_loaded_as_json = True
                try:
                    self._body_as_json = json.loads(self.get_body())
                except json.JSONDecodeError:
                    self._body_as_json = None
        return self._body_as_json

    @abstractmethod
    def get_request_method(self):
        pass

    @abstractmethod
    def get_script_name(self):
        pass

    @abstractmethod
    def get_path_info(self):
        pass

    def get_full_path(self):
        path_info = self.get_path_info()
        script_name = self.get_script_name()
        if not path_info or path_info[0] != "/":
            path_info = f"/{path_info}"
        return f"{path_info}{script_name}".replace("//", "/")

    @abstractmethod
    def get_query_string(self):
        pass

    @abstractmethod
    def get_content_type(self):
        pass

    @abstractmethod
    def get_protocol(self):
        pass

    @abstractmethod
    def has_request_header(self, header_name):
        pass

    @abstractmethod
    def get_request_header(self, header_name, silent=True):
        pass

    @abstractmethod
    def get_query_parameter(self, key):
        pass

    @abstractmethod
    def get_query_parameters(self):
        pass

    @abstractmethod
    def get_client_ip(self):
        pass

    def set_authorization_data(self, data):
        self._authorization_data = data

    def get_authorization_data(self):
        return self._authorization_data if self._authorization_data else {}

    def context_specifics(self):
        return {}
