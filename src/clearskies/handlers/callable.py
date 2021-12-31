from collections import OrderedDict
from .base import Base
from .exceptions import InputError
import inspect
import json
from ..functional import validations


class FakeModel:
    def __getattr__(self, key):
        return None

class Callable(Base):
    _columns = None

    _global_configuration_defaults = {
        'response_headers': None,
        'authentication': None,
        'authorization': None,
        'callable': None,
        'schema': None,
        'writeable_columns': None,
        'id_column_name': None,
        'doc_description': '',
        'internal_casing': '',
        'external_casing': '',
    }

    def __init__(self, di):
        super().__init__(di)

    def handle(self, input_output):
        self._di.bind('input_output', input_output)
        if self.configuration('schema'):
            request_data = self.request_data(input_output)
            input_errors = {
                **self._extra_column_errors(request_data),
                **self._find_input_errors(request_data),
            }
            if input_errors:
                raise InputError(input_errors)
            response = self._di.call_function(self.configuration('callable'), request_data=request_data)
        else:
            response = self._di.call_function(self.configuration('callable'))
        if response is not None:
            return self.success(input_output, response)

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        error_prefix = 'Configuration error for %s:' % (self.__class__.__name__)
        if not 'callable' in configuration:
            raise KeyError(f"{error_prefix} you must specify 'callable'")
        if not callable(configuration['callable']):
            raise ValueError(f"{error_prefix} the provided callable is not actually callable")
        if configuration.get('schema') is not None:
            self._check_schema(configuration['schema'], configuration.get('writeable_columns'), error_prefix)

    def _finalize_configuration(self, configuration):
        if configuration.get('schema') is not None:
            configuration['schema'] = self._schema_to_columns(
                configuration['schema'],
                columns_to_keep=configuration.get('writeable_columns')
            )
        return configuration

    def _find_input_errors(self, input_data):
        input_errors = {}
        fake_model = FakeModel()
        for column in self.configuration('schema').values():
            input_errors = {
                **input_errors,
                **column.input_errors(fake_model, input_data),
            }
        return input_errors

    def _extra_column_errors(self, input_data):
        input_errors = {}
        allowed = self.configuration('schema')
        for column_name in input_data.keys():
            if column_name not in allowed:
                input_errors[column_name] = f"Input column '{column_name}' is not an allowed column"
        return input_errors

    def request_data(self, input_output, required=True):
        # we have to map from internal names to external names, because case mapping
        # isn't always one-to-one, so we want to do it exactly the same way that the documentation
        # is built.
        key_map = {
            self.auto_case_column_name(key, True): key for key in self.configuration('schema').keys()
        }
        # in case the id comes up in the request body
        key_map[self.auto_case_internal_column_name('id')] = 'id'

        # and make sure we don't drop any data along the way, because the input validation
        # needs to return an error for unexpected data.
        request_data = {
            key_map.get(key, key): value
            for (key, value) in input_output.request_data(required=required).items()
        }
        # the parent handler should provide our resource id (we don't do any routing ourselves)
        # However, our update/etc handlers need to find the id easily, so I'm going to be lazy and
        # just dump it into the request.  I'll probably regret that.
        routing_data = input_output.routing_data()
        # we don't have to worry about casing on the 'id' in routing_data because it doesn't come in from the
        # route with a name.  Rather, it is populated by clearskies, so will always just be 'id'
        if 'id' in routing_data:
            request_data['id'] = routing_data['id']
        return request_data

    def _check_schema(self, schema, writeable_columns, error_prefix):
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
        is_valid_schema = False
        if validations.is_model_or_class(schema):
            is_valid_schema = True
        else:
            if not hasattr(schema, '__iter__') or type(schema) ==  str:
                raise ValueError(
                    f"{error_prefix} 'schema' should be a list of column definitions, but was instead a " + type(schema)
                )
            for column in schema:
                if type(column) != tuple:
                    raise ValueError(
                        f"{error_prefix} 'schema' should be a list of column definitions, but one of the entries was not a column definition"
                    )
            is_valid_schema = True
        if not is_valid_schema:
            raise ValueError(f"{error_prefix} 'schema' should be a model, model class, or list of column definitions, but was instead a " + type(schema))

        if not writeable_columns and writeable_columns is not None:
            raise ValueError(f"{error_prefix} 'writeable_columns' can't be an empty list.  It can be 'None', but otherwise I don't know how to handle empty values")

        if writeable_columns:
            if not hasattr(writeable_columns, '__iter__') or type(writeable_columns) == str:
                raise ValueError(
                    f"{error_prefix} 'writeable_columns' should be a list of column names, but was instead a " + type(writeable_columns)
                )
            columns = self._schema_to_columns(schema)
            for column in writeable_columns:
                if type(column) != str:
                    raise ValueError(
                        f"{error_prefix} 'writeable_columns' should be a list of column names, but one of the entries was not a string"
                    )
                if column not in columns:
                    raise ValueError(f"{error_prefix} 'writeable_columns' references a column named '{column}' but this column does not exist in the schema")

    def _schema_to_columns(self, schema, columns_to_keep=None):
        """
        Converts the schema from the developer to a columns object
        """
        # the schema can be a model, model class, or list of column configs.
        # Each requires a different conversion method
        if validations.is_model(schema):
            columns = schema.columns()
        elif validations.is_model_class(schema):
            columns = self._di.build(schema).columns()
        else:
            columns = self._di.build('columns').configure(OrderedDict(schema), self.__class__)

        # if we don't have a list of columns to keep, then we're done
        if not columns_to_keep:
            return columns

        # only keep things that we're allowed to keep
        return OrderedDict([(key, value) for (key, value) in columns.items() if key in columns_to_keep])
