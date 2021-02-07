from .base import Base
from .exceptions import InputError
from collections import OrderedDict
from abc import abstractmethod


class Write(Base):
    _request = None
    _models = None
    _authentication = None
    _writeable_columns = None
    _readable_columns = None

    _configuration_defaults = {
        'columns': None,
        'writeable_columns': None,
        'readable_columns': None,
    }

    def __init__(self, request, authentication, models):
        super().__init__(request, authentication)
        self._models = models

    @abstractmethod
    def handle(self):
        pass

    def _check_configuration(self, configuration):
        has_columns = 'columns' in configuration and configuration['columns'] is not None
        has_writeable = 'writeable_columns' in configuration and configuration['writeable_columns'] is not None
        has_readable = 'readable_columns' in configuration and configuration['readable_columns'] is not None
        error_prefix = 'Configuration error for %s:' % (self.__class__.__name__)
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
            if type(configuration[config_name]) == list:
                continue
            raise ValueError(
                f"{error_prefix} '{config_name}' should be a list of column names " +
                f", not {str(type(configuration['columns']))}"
            )

        if has_columns and not configuration['columns']:
            raise KeyError(f"{error_prefix} you must specify at least one column for 'columns'")
        if has_writeable and not configuration['writeable_columns']:
            raise KeyError(f"{error_prefix} you must specify at least one column for 'writeable_columns'")
        if has_readable and not configuration['readable_columns']:
            raise KeyError(f"{error_prefix} you must specify at least one column for 'readable_columns'")

    def _get_rw_columns(self, columns, rw_type):
        column_names = self.configuration('columns')
        if column_names is None:
            column_names = self.configuration(f'{rw_type}_columns')
        wr_columns = OrderedDict()
        for column_name in column_names:
            if column_name not in columns:
                class_name = self.__class__.__name__
                model_class = self._models.model_class().__name__
                raise ValueError(
                    f"Handler {class_name} was configured with {rw_type} column '{column_name}' but this " +
                    f"column doesn't exist for model {model_class}"
                )
            wr_columns[column_name] = columns[column_name]
        return wr_columns

    def _get_writeable_columns(self, columns):
        if self._writeable_columns is None:
            self._writeable_columns = self._get_rw_columns(columns, 'writeable')
        return self._writeable_columns

    def _get_readable_columns(self, columns):
        if self._readable_columns is None:
            self._readable_columns = self._get_rw_columns(columns, 'readable')
        return self._readable_columns

    def _extra_column_errors(self, input_data, columns):
        input_errors = {}
        allowed = self._get_writeable_columns(columns)
        for column_name in input_data.keys():
            if column_name not in allowed:
                input_errors[column_name] = f"Input column '{column_name}' is not an allowed column"
        return input_errors

    def _find_input_errors(self, model, input_data, columns):
        input_errors = {}
        for column in self._get_writeable_columns(columns).values():
            input_errors = {
                **input_errors,
                **column.input_errors(model, input_data),
            }
        return input_errors

    def _model_as_json(self, model, columns):
        json = OrderedDict()
        json['id'] = int(model.id)
        for column in self._get_readable_columns(columns).values():
            json[column.name] = column.to_json(model)
        return json
