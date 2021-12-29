from .base import Base
import inspect
import json
from ..functional import validations


class Callable(Base):
    _global_configuration_defaults = {
        'authentication': None,
        'callable': None,
        'schema': None,
    }

    def __init__(self, di):
        super().__init__(di)

    def handle(self, input_output):
        self._di.bind('input_output', input_output)
        response = self._di.call_function(self.configuration('callable'))
        if response is not None:
            if type(response) == dict or type(response) == list:
                return input_output.success(json.dumps(response))
            return input_output.success(response)

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        error_prefix = 'Configuration error for %s:' % (self.__class__.__name__)
        if not 'callable' in configuration:
            raise KeyError(f"{error_prefix} you must specify 'callable'")
        if not callable(configuration['callable']):
            raise ValueError(f"{error_prefix} the provided callable is not actually callable")
        if configuration.get('schema') is not None:
            self._check_schema(configuration['schema'])

    def _check_schema(self, schema):
        """
        Validates that the schema provided in the configuration is valid.

        The schema is allowed to be one of 3 things:

        1. A list of column definitions.
        2. A model class.
        3. A model.

        An example of option #1 would be:

        ```
        {
            'schema': [
                clearskies.column_types.string('name', input_requirements=[clearskies.input_requirements.required()]),
                clearskies.column_types.integer('age'),
            ],
        }
        ```
        """
        if validations.is_model_or_class(schema):
            return
        # check the schema!
