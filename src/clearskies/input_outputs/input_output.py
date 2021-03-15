from abc import ABC, abstractmethod
from collections import OrderedDict
import json


class InputOutput(ABC):
    _response_headers = None
    _body_as_json = None
    _body_loaded_as_json = False

    @abstractmethod
    def respond(self, body, status_code=200):
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
        for (key, value) in headers.items():
            self.set_header(key, value)

    @abstractmethod
    def get_body(self):
        pass

    @abstractmethod
    def has_body(self):
        pass

    def get_json_body(self):
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
    def get_path_info(self):
        pass

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
