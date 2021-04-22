from abc import ABC, abstractmethod
from .exceptions import ClientError, InputError
from collections import OrderedDict


class Base(ABC):
    _configuration = None
    _configuration_defaults = {}
    _global_configuration_defaults = {
        'response_headers': None,
        'authentication': None,
    }
    _input_output = None
    _object_graph = None
    _configuration = None

    def __init__(self, input_output, object_graph):
        self._input_output = input_output
        self._object_graph = object_graph
        self._configuration = None

    @abstractmethod
    def handle(self):
        pass

    def configure(self, configuration):
        for key in configuration.keys():
            if key not in self._configuration_defaults and key not in self._global_configuration_defaults:
                class_name = self.__class__.__name__
                raise KeyError(f"Attempt to set unkown configuration setting '{key}' for handler '{class_name}'")

        self._check_configuration(configuration)
        self._configuration = self._finalize_configuration(self.apply_default_configuation(configuration))

    def _check_configuration(self, configuration):
        if not 'authentication' in configuration:
            raise KeyError(
                f"You must provide authentication in the configuration for handler '{self.__class__.__name__}'"
            )

    def apply_default_configuation(self, configuration):
        return {
            **self._global_configuration_defaults,
            **self._configuration_defaults,
            **configuration,
        }

    def configuration(self, key):
        if self._configuration is None:
            raise ValueError("Cannot fetch configuration values before setting the configuration")
        if key not in self._configuration:
            class_name = self.__class__.__name__
            raise KeyError(f"Configuration key '{key}' does not exist for handler '{class_name}'")
        return self._configuration[key]

    def _finalize_configuration(self, configuration):
        configuration['authentication'] = self._object_graph.build(configuration['authentication'])
        return configuration

    def __call__(self):
        if self._configuration is None:
            raise ValueError("Must configure handler before calling")
        if not self.configuration('authentication').authenticate():
            return self.error('Not Authenticated', 401)

        try:
            response = self.handle()
        except ClientError as client_error:
            return self.error(str(client_error), 400)
        except InputError as input_error:
            return self.input_errors(input_error.errors)

        return response

    def input_errors(self, errors, status_code=200):
        return self.respond({'status': 'inputErrors', 'inputErrors': errors}, status_code)

    def error(self, message, status_code):
        return self.respond({'status': 'clientError', 'error': message}, status_code)

    def success(self, data, number_results=None, start=None, limit=None):
        response_data = {'status': 'success', 'data': data, 'pagination': {}}

        if number_results is not None:
            for value in [number_results, start, limit]:
                if value is not None and type(value) != int:
                    raise ValueError("number_results, start, and limit must all be integers")

            response_data['pagination'] = {
                'numberResults': number_results,
                'start': start,
                'limit': limit
            }

        return self.respond(response_data, 200)

    def respond(self, response_data, status_code):
        response_headers = self.configuration('response_headers')
        if response_headers:
            self._input_output.set_headers(response_headers)
        return self._input_output.respond(self._normalize_response(response_data), status_code)

    def _normalize_response(self, response_data):
        if not 'status' in response_data:
            raise ValueError("Huh, status got left out somehow")
        if not 'error' in response_data:
            response_data['error'] = ''
        if not 'data' in response_data:
            response_data['data'] = []
        if not 'pagination' in response_data:
            response_data['pagination'] = {}
        if not 'inputErrors' in response_data:
            response_data['inputErrors'] = {}
        return response_data

    def request_data(self, required=True):
        request_data = self.json_body(False)
        if not request_data:
            if self._input_output.has_body():
                raise ClientError("Request body was not valid JSON")
            request_data = {}
        return request_data

    def json_body(self, required=True):
        json = self._input_output.get_json_body()
        # if we get None then either the body was not JSON or was empty.
        # If it is required then we have an exception either way.  If it is not required
        # then we have an exception if a body was provided but it was not JSON.  We can check for this
        # if json is None and there is an actual request body.  If json is none, the body is empty,
        # and it was not required, then we can just return None
        if json is None:
            if required or self._input_output.has_body():
                raise ClientError("Request body was not valid JSON")
        return json

    def _model_as_json(self, model):
        json = OrderedDict()
        json['id'] = int(model.id)
        for column in self._get_readable_columns().values():
            json[column.name] = column.to_json(model)
        return json
