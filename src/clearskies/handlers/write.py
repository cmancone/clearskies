from .base import Base
from .exceptions import InputError
from collections import OrderedDict
from abc import abstractmethod
from .. import autodoc
from ..functional import string
import inspect
class Write(Base):
    _di = None
    _model = None
    _columns = None
    _authentication = None
    _writeable_columns = None
    _readable_columns = None

    _configuration_defaults = {
        'model': None,
        'model_class': None,
        'columns': None,
        'writeable_columns': None,
        'readable_columns': None,
    }

    def __init__(self, di):
        super().__init__(di)

    @abstractmethod
    def handle(self, input_output):
        pass

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        error_prefix = 'Configuration error for %s:' % (self.__class__.__name__)
        has_model_class = ('model_class' in configuration) and configuration['model_class'] is not None
        has_model = ('model' in configuration) and configuration['model'] is not None
        if not has_model and not has_model_class:
            raise KeyError(f"{error_prefix} you must specify 'model' or 'model_class'")
        if has_model and has_model_class:
            raise KeyError(f"{error_prefix} you specified both 'model' and 'model_class', but can only provide one")
        if has_model and inspect.isclass(configuration['model']):
            raise ValueError(
                "{error_prefix} you must provide a model instance in the 'model' configuration setting, but a class was provided instead"
            )
        self._model = self._di.build(configuration['model_class']) if has_model_class else configuration['model']
        self._columns = self._model.columns(overrides=configuration.get('overrides'))
        has_columns = 'columns' in configuration and configuration['columns'] is not None
        has_writeable = 'writeable_columns' in configuration and configuration['writeable_columns'] is not None
        has_readable = 'readable_columns' in configuration and configuration['readable_columns'] is not None
        if not has_columns and not has_writeable:
            raise KeyError(f"{error_prefix} you must specify 'columns' OR 'writeable_columns'")
        if not has_columns and not has_readable:
            raise KeyError(f"{error_prefix} you must specify 'columns' OR 'readable_columns'")
        if has_columns and has_writeable:
            raise KeyError(f"{error_prefix} you must specify 'columns' OR 'writeable_columns', not both")
        if has_columns and has_readable:
            raise KeyError(f"{error_prefix} you must specify 'columns' OR 'readable_columns', not both")
        if has_writeable and not has_readable:
            raise KeyError(f"{error_prefix} you must specify 'readable_columns' if you specify 'writeable_columns'")
        if has_readable and not has_writeable:
            raise KeyError(f"{error_prefix} you must specify 'writeable_columns' if you specify 'readable_columns'")

        for config_name in ['columns', 'writeable_columns', 'readable_columns']:
            if config_name not in configuration or configuration[config_name] is not None:
                continue
            if hasattr(configuration[config_name], '__iter__'):
                continue
            raise ValueError(
                f"{error_prefix} '{config_name}' should be a list of column names " +
                f", not {str(type(configuration[config_name]))}"
            )

        if has_columns and not configuration['columns']:
            raise KeyError(f"{error_prefix} you must specify at least one column for 'columns'")
        if has_writeable and not configuration['writeable_columns']:
            raise KeyError(f"{error_prefix} you must specify at least one column for 'writeable_columns'")
        if has_readable and not configuration['readable_columns']:
            raise KeyError(f"{error_prefix} you must specify at least one column for 'readable_columns'")
        writeable_columns = configuration['writeable_columns'] if has_writeable else configuration['columns']
        for column_name in writeable_columns:
            if column_name not in self._columns:
                raise KeyError(f"{error_prefix} specified writeable column '{column_name}' does not exist")
            if not self._columns[column_name].is_writeable:
                raise KeyError(f"{error_prefix} specified writeable column '{column.name}' is not writeable")
        readable_columns = configuration['readable_columns'] if has_readable else configuration['columns']
        for column_name in readable_columns:
            if column_name not in self._columns:
                raise KeyError(f"{error_prefix} specified readable column '{column_name}' does not exist")

    def _get_rw_columns(self, rw_type):
        column_names = self.configuration('columns')
        if column_names is None:
            column_names = self.configuration(f'{rw_type}_columns')
        wr_columns = OrderedDict()
        for column_name in column_names:
            if column_name not in self._columns:
                class_name = self.__class__.__name__
                model_class = self._model.__class__.__name__
                raise ValueError(
                    f"Configuration error for {self.__class__.__name__}: handler was configured with {rw_type} " + \
                    f"column '{column_name}' but this column doesn't exist for model {model_class}"
                )
            wr_columns[column_name] = self._columns[column_name]
        return wr_columns

    def _get_writeable_columns(self):
        if self._writeable_columns is None:
            self._writeable_columns = self._get_rw_columns('writeable')
        return self._writeable_columns

    def _get_readable_columns(self):
        if self._readable_columns is None:
            self._readable_columns = self._get_rw_columns('readable')
        return self._readable_columns

    def _extra_column_errors(self, input_data):
        input_errors = {}
        allowed = self._get_writeable_columns()
        for column_name in input_data.keys():
            if column_name not in allowed:
                input_errors[column_name] = f"Input column '{column_name}' is not an allowed column"
        return input_errors

    def _find_input_errors(self, model, input_data):
        input_errors = {}
        for column in self._get_writeable_columns().values():
            input_errors = {
                **input_errors,
                **column.input_errors(model, input_data),
            }
        return input_errors

    def request_data(self, input_output, required=True):
        # we have to map from internal names to external names, because case mapping
        # isn't always one-to-one, so we want to do it exactly the same way that the documentation
        # is built.
        key_map = {self.auto_case_column_name(key, True): key for key in self._get_writeable_columns().keys()}
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

    def documentation_models(self):
        schema_model_name = string.camel_case_to_snake_case(self._model.__class__.__name__)

        return {
            schema_model_name: autodoc.schema.Object(
                'data',
                children=self.documentation_data_schema(),
            ),
        }

    def _documentation(self, description='', response_description='', include_id_in_path=False):
        nice_model = string.camel_case_to_words(self._model.__class__.__name__)
        data_schema = self.documentation_data_schema()
        schema_model_name = string.camel_case_to_snake_case(self._model.__class__.__name__)

        authentication = self.configuration('authentication')
        standard_error_responses = [
            self.documentation_input_error_response(),
        ]
        if not getattr(authentication, 'is_public', False):
            standard_error_responses.append(self.documentation_access_denied_response())
            if getattr(authentication, 'can_authorize', False):
                standard_error_responses.append(self.documentation_unauthorized_response())

        url = self.configuration('base_url')
        if include_id_in_path:
            url = url.rstrip('/') + '/{id}'

        return [
            autodoc.request.Request(
                description,
                [
                    self.documentation_success_response(
                        autodoc.schema.Object(
                            self.auto_case_internal_column_name('data'),
                            children=data_schema,
                            model_name=schema_model_name,
                        ),
                        description=description,
                    ),
                    *standard_error_responses,
                    self.documentation_not_found(),
                ],
                relative_path=url,
                parameters=[
                    *self.documentation_write_parameters(nice_model),
                ],
                root_properties={
                    'security': self.documentation_request_security(),
                },
            )
        ]

    def documentation_write_parameters(self, model_name):
        return [
            autodoc.request.JSONBody(
                column.documentation(name=self.auto_case_column_name(column.name, True)),
                description=f"Set '{column.name}' for the {model_name}",
                required=column.is_required,
            ) for column in self._get_writeable_columns().values()
        ]
