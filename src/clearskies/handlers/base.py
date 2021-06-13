from abc import ABC, abstractmethod
from .exceptions import ClientError, InputError
from collections import OrderedDict
import inspect


class Base(ABC):
    _configuration = None
    _configuration_defaults = {}
    _global_configuration_defaults = {
        'base_url': '',
        'response_headers': None,
        'authentication': None,
        'authorization': None,
        'output_map': None,
        'column_overrides': None,
    }
    _di = None
    _configuration = None

    def __init__(self, di):
        self._di = di
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
        if configuration.get('authorization', None):
            if not callable(configuration['authorization']) and not isinstance(configuration['authorization'], dict):
                raise ValueError("'authorization' should be a callable or a dictionary with subclaims to enforce")
        if configuration.get('output_map') is not None:
            if not callable(configuration['output_map']):
                raise ValueError("'output_map' should be a callable")
            signature = inspect.getfullargspec(configuration['output_map'])
            if signature.defaults and len(signature.defaults):
                raise ValueError(
                    "'output_map' should be a callable that accepts one parameter: the model. " + \
                    "However, the provided one accepts kwargs"
                )
            if len(signature.args) != 1:
                raise ValueError(
                    "'output_map' should be a callable that accepts one parameter: the model. " + \
                    f"However, the provided one accepts {len(signature.args)}"
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
        configuration['authentication'] = self._di.build(configuration['authentication'])
        return configuration

    def __call__(self, input_output):
        if self._configuration is None:
            raise ValueError("Must configure handler before calling")
        authentication = self._configuration.get('authentication')
        if authentication:
            try:
                if not authentication.authenticate(input_output):
                    return self.error(input_output, 'Not Authenticated', 401)
            except ClientError as client_error:
                return self.error(input_output, str(client_error), 400)
            authorization = self._configuration.get('authorization')
            if authorization:
                try:
                    if not authentication.authorize(authorization):
                        return self.error(input_output, 'Not Authorized', 401)
                except ClientError as client_error:
                    return self.error(input_output, str(client_error), 400)

        try:
            response = self.handle(input_output)
        except ClientError as client_error:
            return self.error(input_output, str(client_error), 400)
        except InputError as input_error:
            return self.input_errors(input_output, input_error.errors)

        return response

    def input_errors(self, input_output, errors, status_code=200):
        return self.respond(input_output, {'status': 'inputErrors', 'inputErrors': errors}, status_code)

    def error(self, input_output, message, status_code):
        return self.respond(input_output, {'status': 'clientError', 'error': message}, status_code)

    def success(self, input_output, data, number_results=None, start=None, limit=None):
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

        return self.respond(input_output, response_data, 200)

    def respond(self, input_output, response_data, status_code):
        response_headers = self.configuration('response_headers')
        if response_headers:
            input_output.set_headers(response_headers)
        return input_output.respond(self._normalize_response(response_data), status_code)

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

    def _model_as_json(self, model):
        if self.configuration('output_map'):
            return self.configuration('output_map')(model)

        json = OrderedDict()
        json['id'] = int(model.id)
        for column in self._get_readable_columns().values():
            json[column.name] = column.to_json(model)
        return json
