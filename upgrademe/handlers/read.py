from .base import Base
from collections import OrderedDict


class Read(Base):
    _request = None
    _models = None
    _columns = None
    _authentication = None
    _searchable_columns = None
    _readable_columns = None

    _configuration_defaults = {
        'readable_columns': None,
        'searchable_columns': None,
        'sortable_columns': [],
        'where': [],
        'join': [],
        'group_by': '',
        'default_sort_column': '',
        'default_sort_direction': 'asc',
        'default_page_length': 100,
        'max_page_length': 200,
    }

    def __init__(self, request, authentication, models):
        super().__init__(request, authentication)
        self._models = models
        self._columns = self._models.columns()

    def handle(self):
        # first configure our models object with the defaults
        models = self._models
        for where in self.configuration('where'):
            models = models.where(where)
        for join in self.configuration('join'):
            models = models.join(join)
        if self.configuration('group_by'):
            models = models.group_by(self.configuration('group_by'))

        request_data = self.json_body(self, False)
        if request_data:
            error = self._check_request_data(request_data)
            if error:
                return self.error(error, 400)

    def _check_request_data(self, request_data):
        # first, check that they didn't provide something unexpected
        allowed_request_keys = ['where', 'sort', 'direction', 'page', 'limit']
        for key in request_data.keys():
            if key not in allowed_request_keys:
                return f"Invalid request parameter: '{key}'"
        for key_name in ['page', 'limit']:
            if key_name in request_data and type(request_data[key_name]) != int:
                return f"Invalid request data: '{key_name}' should be an integer"
        if 'direction' in request_data:
            if type(request_data['direction']) != str:
                return f"Invalid request data: 'direction' should be a string"
            normalized_direction = request_data['direction'].strip().lower()
            if normalized_direction != 'asc' and normalized_direction != 'desc':
                return f"Invalid request data: 'direction' should be 'asc' or 'desc'"

    def _check_configuration(self, configuration):
        error_prefix = 'Configuration error for %s:' % (self.__class__.__name__)
        model_class_name = str(self._models.model_class())
        # checks for searchable_columns and readable_columns
        for config_name in ['searchable_columns', 'readable_columns']:
            if not config_name in configuration or not configuration[config_name]:
                raise ValueError(f"{error_prefix} missing required configuration '{config_name}'")
            if not hasattr(configuration[config_name], '__iter__'):
                raise ValueError(
                    f"{error_prefix} '{config_name}' should be an iterable of column names " +
                    f", not {str(type(configuration[config_name]))}"
                )
            for column_name in configuration[config_name]:
                if column_name not in self._columns:
                    raise ValueError(
                        f"{error_prefix} '{config_name}' references column named {column_name} " +
                        f"but this column does not exist for model '{model_class_name}'"
                    )

        # sortable_columns, wheres, and joins should all be iterables
        for config_name in ['sortable_columns', 'where', 'join']:
            if not hasattr(configuration[config_name], '__iter__'):
                raise ValueError(
                    f"{error_prefix} '{config_name}' should be an iterable of column names " +
                    f", not {str(type(configuration[config_name]))}"
                )

        # checks for sortable_columns
        for column_name in configuration['sortable_columns']:
            if column_name not in self._columns:
                raise ValueError(
                    f"{error_prefix} 'sortable_columns' references column named {column_name} " +
                    f"but this column does not exist for model '{model_class_name}'"
                )

        # common checks for group_by and default_sort_column
        for config_name in ['group_by', 'default_sort_column']:
            if configuration[config_name] and configuration[config_name] not in self._columns:
                raise ValueError(
                    f"{error_prefix} '{config_name}' references column named {column_name} " +
                    f"but this column does not exist for model '{model_class_name}'"
                )

        for config_name in ['default_page_length', 'max_page_length']:
            if type(configuration[config_name]) != int:
                raise ValueError(
                    f"{error_prefix} '{config_name}' should be an int, not {str(type(configuration[config_name]))}"
                )

    def _get_columns(self, columns, column_type):
        resolved_columns = OrderedDict()
        for column_name in self.configuration(f'{column_type}_columns'):
            if column_name not in columns:
                class_name = self.__class__.__name__
                model_class = self._models.model_class().__name__
                raise ValueError(
                    f"Handler {class_name} was configured with {column_type} column '{column_name}' but this " +
                    f"column doesn't exist for model {model_class}"
                )
            resolved_columns[column_name] = columns[column_name]
        return resolved_columns

    def _get_readable_columns(self, columns):
        if self._readable_columns is None:
            self._readable_columns = self._get_columns(columns, 'readable')
        return self._readable_columns

    def _get_searchable_columns(self, columns):
        if self._searchable_columns is None:
            self._searchable_columns = self._get_columns(columns, 'searchable')
        return self._searchable_columns
