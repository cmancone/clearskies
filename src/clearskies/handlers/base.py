from abc import ABC, abstractmethod
from .exceptions import ClientError, InputError
from collections import OrderedDict
import inspect
import re
from ..autodoc.schema import Integer as AutoDocInteger
from ..autodoc.schema import String as AutoDocString
from ..autodoc.schema import Object as AutoDocObject
from ..autodoc.response import Response as AutoDocResponse
from ..functional import string


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
        'id_column_name': None,
        'doc_description': '',
        'internal_casing': '',
        'external_casing': '',
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
        number_casings = 0
        internal_casing = configuration.get('internal_casing')
        if internal_casing is not None and internal_casing:
            raise ValueError(
                f"Invalid internal_casing config for handler '{self.__class__.__name__}': expected one of " + \
                "'" + ", '".join(string.casings) + f"' but found '{internal_casing}'"
            )
            number_casings += 1
        external_casing = configuration.get('external_casing')
        if external_casing is not None and external_casing:
            raise ValueError(
                f"Invalid external_casing config for handler '{self.__class__.__name__}': expected one of " + \
                "'" + ", '".join(string.casings) + f"' but found '{external_casing}'"
            )
            number_casings += 1
        if number_casings == 1:
            raise ValueError(
                f"Configuration error for handler '{self.__class__.__name__}': external_casing and internal_casing" + \
                " must be specified together, but only one was found"
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
                return self.error(input_output, str(client_error), 401)
            authorization = self._configuration.get('authorization')
            if authorization:
                try:
                    if not authentication.authorize(authorization):
                        return self.error(input_output, 'Not Authorized', 403)
                except ClientError as client_error:
                    return self.error(input_output, str(client_error), 403)

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

        model_id = getattr(model, self.id_column_name)
        json = OrderedDict()
        json['id'] = model_id
        for column in self._get_readable_columns().values():
            json[self.auto_case_column_name(column.name, True)] = column.to_json(model)
        return json

    def auto_case_column_name(self, column_name, internal_to_external):
        if not self._configuration['internal_casing']:
            return column_name
        if internal_to_external:
            return string.swap_casing(
                column_name,
                self._configuration['internal_casing'],
                self._configuration['external_casing'],
            )
        return string.swap_casing(
            column_name,
            self._configuration['external_casing'],
            self._configuration['internal_casing'],
        )


    @property
    def id_column_name(self) -> str:
        """
        This returns the name of the id column to use for requests

        There are three ways to determine the id column:

         1. It may be defined in the handler configuration.
         2. It may be overridden in the model class
         3. It defaults to 'id'

        The first happens if the developer wants to expose a different "id" column to the client.
        The second happens if the developer wants to use a different id column internally.
        The third is the clearskies default.

        The first is easy to detect because the dev will set `id_column_name` in the handler config.
        The second happens if the model class defines a different `id_column_name` property in the model class.
        However, this is tricky because there is nothing in this base case that allows us to pull up the model.
        In fact, not all handlers use a model, or they may use multiple models, etc...  Still, it's pretty
        common for the handler to have a configuration named `model_class` or `model`, so let's check for that and assume
        the handler will only ask for the id_column_name() if the handler has a `self.configuration('model_class')`
        """
        id_column_name = self.configuration('id_column_name')
        if id_column_name is not None:
            return id_column_name
        if not self._configuration.get('model_class', False) and not self._configuration.get('model', False):
            raise KeyError(
                "To properly use handler.id_column_name, the handler must have a 'model_class' or 'model' configuration key"
            )
        if self._configuration.get('model_class', False):
            return self._configuration.get('model_class').id_column_name
        return self._configuration.get('model').id_column_name

    def documentation(self):
        return []

    def documentation_models(self):
        return {}

    def documentation_pagination_response(self, include_pagination=True):
        if not include_pagination:
            return AutoDocObject('pagination', [], value={})
        return AutoDocObject(
            'pagination',
            [
                AutoDocInteger('numberResults', example=10),
                AutoDocInteger('start', example=0),
                AutoDocInteger('limit', example=100),
            ],
        )

    def documentation_success_response(self, data_schema, description='', include_pagination=False):
        return AutoDocResponse(
            200,
            AutoDocObject(
                'body',
                [
                    AutoDocString('status', value='success'),
                    data_schema,
                    self.documentation_pagination_response(include_pagination=include_pagination),
                    AutoDocString('error', value=''),
                    AutoDocObject('inputErrors', [], value={}),
                ]
            ),
            description=description,
        )

    def documentation_generic_error_response(self, description='Invalid Call', status=400):
        return AutoDocResponse(
            status,
            AutoDocObject(
                'body',
                [
                    AutoDocString('status', value='error'),
                    AutoDocObject('data', [], value={}),
                    self.documentation_pagination_response(),
                    AutoDocString('error', example='User readable error message'),
                    AutoDocObject('inputErrors', [], value={}),
                ]
            ),
            description=description
        )

    def documentation_input_error_response(self, description='Invalid client-side input'):
        return AutoDocResponse(
            200,
            AutoDocObject(
                'body',
                [
                    AutoDocString('status', value='inputErrors'),
                    AutoDocObject('data', [], value={}),
                    self.documentation_pagination_response(),
                    AutoDocString('error', value=''),
                    AutoDocObject(
                        'inputErrors',
                        [
                            AutoDocString('[COLUMN_NAME]', example='User friendly error message')
                        ],
                        example={'email': 'email was not a valid email address'}
                    ),
                ]
            ),
            description=description
        )

    def documentation_access_denied_response(self):
        return self.documentation_generic_error_response(description='Access Denied', status=401)

    def documentation_unauthorized_response(self):
        return self.documentation_generic_error_response(description='Unauthorized', status=403)

    def documentation_not_found(self):
        return self.documentation_generic_error_response(description='Not Found', status=404)

    def documentation_data_schema(self):
        id_column_name = self.id_column_name
        properties = [
            self._columns[id_column_name].documentation(name='id') if id_column_name in self._columns else AutoDocString('id')
        ]

        for column in self._get_readable_columns().values():
            properties.append(column.documentation())

        return properties
