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
        'default_limit': 100,
        'max_limit': 200,
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
        models = models.limit(0, self.configuration('default_limit'))

        request_data = self.json_body(self, False)
        if request_data:
            error = self._check_request_data(request_data)
            if error:
                return self.error(error, 400)
            models = self._configure_models_from_request_data(models, request_data)

        return self.success({
            [self._model_as_json(model, self._columns) for model in models],
            number_results=len(models),
            page_length=None,
            page_number=None
        })

    def _configure_models_from_request_data(self, models, request_data):
        start = 0
        limit = self.configuration('default_limit')
        if 'start' in request_data:
            start = request_data['start']
        if 'limit' in request_data:
            limit = request_data['limit']
        models = models.limit(start, limit)
        if 'sort' in request_data:
            primary_column = request_data['sort'][0]['column']
            primary_direction = request_data['sort'][0]['direction']
            secondary_column = None
            secondary_direction = None
            if len(request_data['sort']) == 2:
                secondary_column = request_data['sort'][1]['column']
                secondary_direction = request_data['sort'][1]['direction']
            models = models.sort_by(
                primary_column,
                primary_direction,
                secondary_column=secondary_column,
                secondary_direction=secondary_direction
            )
        if 'where' in request_data:
            for where in request_data['where']:
                column = self._columns[where['column']]
                models = models.where(
                    column.build_condition(
                        where['value'],
                        operator=where['operator'] if 'operator' in where else None
                    )
                )
        return models


    def _check_request_data(self, request_data):
        # first, check that they didn't provide something unexpected
        allowed_request_keys = ['where', 'sort', 'start', 'limit']
        for key in request_data.keys():
            if key not in allowed_request_keys:
                return f"Invalid request parameter: '{key}'"
        for key_name in ['start', 'limit']:
            if key_name in request_data and type(request_data[key_name]) != int:
                return f"Invalid request: '{key_name}' should be an integer"
        if 'limit' in request_data and request_data['limit'] > self.configuration('max_limit'):
            return f"Invalid request: 'limit' must be at most {self.configuration('max_limit')}"
        sort = self._fetch_normalized_sort_from_request_data(request_data)
        if 'sort' in request_data:
            if type(request_data['sort']) != list:
                return "Invalid request: if provided, 'sort' must be a list of " + \
                    "objects with 'column' and 'direction' keys"
            if len(request_data['sort']) > 2:
                return "Invalid request: at most 2 sort directives may be specified"
            allowed_sort_columns = self.configuration('sortable_columns')
            if not allowed_sort_columns:
                allowed_sort_columns = self._columns
            for (index, sort) in enumerate(request_data['sort']):
                error_prefix = "Invalid request: 'sort' must be a list of objects with 'column' and 'direction'" + \
                    f" keys, but entry #{index+1}"
                if type(sort) != dict:
                    return f"{error_prefix} was not an object"
                if 'column' not in sort or 'direction' not in sort or not sort['column'] or not sort['direction']:
                    return f"{error_prefix} did not declare both 'column' and 'direction'"
                if len(sort) != 2:
                    return f"{error_prefix} had extra keys present"
                if sort['direction'].lower() not in ['asc', 'desc']:
                    return "Invalid request: sort direction must be 'asc' or 'desc'" + \
                        f" but found something else in sort entry #{index+1}"
                if sort['column'] not in allowed_sort_columns:
                    return f"Invalid request: invalid sort column specified in sort entry #{index+1}"
        if 'where' in request_data:
            if type(request_data['where']) != list:
                return "Invalid request: if provided, 'where' must be a list of objects"
            for (index, where) in enumerate(request_data['where']):
                if type(where) != object:
                    return f"Invalid request: 'where' must be a list of objects, entry #{index+1} was not an object"
                if 'column' not in where or not where['column']:
                    return f"Invalid request: 'column' missing in 'where' entry #{index+1}"
                if where['column'] not in self.configuration('searchable_columns'):
                    return f"Invalid request: invalid search column specified in where entry #{index+1}"
                if 'value' not in where:
                    return f"Invalid request: 'value' missing in 'where' entry #{index+1}"
                if 'operator' in where and not self._columns[where['column']].is_allowed_operator(where['operator']):
                    return f"Invalid request: given operator is not allowed for column in 'where' entry #{index+1}"


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
