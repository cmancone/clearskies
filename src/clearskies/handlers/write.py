from .base import Base
from .exceptions import InputError
from collections import OrderedDict
from abc import abstractmethod


class Write(Base):
    _input_output = None
    _object_graph = None
    _models = None
    _columns = None
    _authentication = None
    _writeable_columns = None
    _readable_columns = None

    _configuration_defaults = {
        'models': None,
        'models_class': None,
        'columns': None,
        'writeable_columns': None,
        'readable_columns': None,
        'resource_id': None,
    }

    def __init__(self, input_output, object_graph):
        super().__init__(input_output, object_graph)

    @abstractmethod
    def handle(self):
        pass

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        error_prefix = 'Configuration error for %s:' % (self.__class__.__name__)
        has_models_class = ('models_class' in configuration) and configuration['models_class'] is not None
        has_models = ('models' in configuration) and configuration['models'] is not None
        if not has_models and not has_models_class:
            raise KeyError(f"{error_prefix} you must specify 'models' or 'models_class'")
        if has_models and has_models_class:
            raise KeyError(f"{error_prefix} you specified both 'models' and 'models_class', but can only provide one")
        self._models = self._object_graph.provide(configuration['models_class']) if has_models_class else configuration['models']
        self._columns = self._models.columns()
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
                model_class = self._models.model_class().__name__
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

    def request_data(self, required=True):
        request_data = super().request_data(required=required)
        if self.configuration('resource_id'):
            request_data['id'] = self.configuration('resource_id')
        return request_data
