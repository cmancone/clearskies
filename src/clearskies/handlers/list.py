from .base import Base
from collections import OrderedDict
from .. import autodoc
from .. import condition_parser
from ..functional import string
import inspect


class List(Base):
    _model = None
    _columns = None
    _searchable_columns = None
    _readable_columns = None

    _configuration_defaults = {
        'model': None,
        'model_class': None,
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
        'single_record': False,
        'debug': False,
    }

    def __init__(self, di):
        super().__init__(di)

    def handle(self, input_output):
        if self.configuration('debug'):
            print('processing read request')
        # first configure our models object with the defaults
        models = self._model
        for where in self.configuration('where'):
            models = models.where(where)
        for join in self.configuration('join'):
            models = models.join(join)
        if self.configuration('group_by'):
            models = models.group_by(self.configuration('group_by'))
        start = 0
        limit = self.configuration('default_limit')
        models = models.limit(start, limit)
        if self.configuration('debug'):
            print('Models config after adding default settings:')
            print(models.configuration)

        request_data = input_output.request_data(False)
        query_parameters = input_output.get_query_parameters()
        if request_data:
            error = self.check_request_data(request_data, query_parameters)
            if error:
                return self.error(input_output, error, 400)
            [models, start, limit] = self.configure_models_from_request_data(models, request_data, query_parameters)
        if not models.query_sorts:
            models = models.sort_by(self.configuration('default_sort_column'), self.configuration('default_sort_direction'))

        if self.configuration('debug'):
            print('Models config after adding user input:')
            print(models.configuration)

        if self.configuration('single_record'):
            if self.configuration('debug'):
                print('Executing single record mode')
            json_output = [self._model_as_json(model) for model in models]
            if not len(json_output):
                return self.error(input_output, 'Record not found', 400)
            return self.success(input_output, json_output[0])

        return self.success(
            input_output,
            [self._model_as_json(model) for model in models],
            number_results=len(models),
            start=start,
            limit=limit,
        )

    def configure_models_from_request_data(self, models, request_data, query_parameters):
        models = models.limit(
            int(self._from_either(request_data, query_parameters, 'start', default=0)),
            int(self._from_either(request_data, query_parameters, 'limit', default=self.configuration('default_limit'))),
        )
        sort = self._from_either(request_data, query_parameters, 'sort')
        direction = self._from_either(request_data, query_parameters, 'direction')
        if sort and direction:
            models = models.sort_by(sort, direction)

        return [models, start, limit]

    @property
    def allowed_request_keys(self):
        return ['sort', 'start', 'limit']

    def check_request_data(self, request_data, query_parameters):
        # first, check that they didn't provide something unexpected
        allowed_request_keys = self.allowed_request_keys
        for key in request_data.keys():
            if key not in allowed_request_keys:
                return f"Invalid request parameter found in request body: '{key}'"
        for key in query_parameters.keys():
            if key not in allowed_request_keys:
                return f"Invalid request parameter found in URL data: '{key}'"
            if key in request_data:
                return f"Ambiguous request: '{key}' was found in both the request body and URL data"
        start = self._from_either(request_data, query_parameters, 'start')
        limit = self._from_either(request_data, query_parameters, 'limit')
        if start:
            try:
                start = int(start)
            except ValueError:
                return "Invalid request: 'start' should be an integer"
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                return "Invalid request: 'limit' should be an integer"
        if limit and limit > self.configuration('max_limit'):
            return f"Invalid request: 'limit' must be at most {self.configuration('max_limit')}"
        allowed_sort_columns = self.configuration('sortable_columns')
        if not allowed_sort_columns:
            allowed_sort_columns = self._columns
        sort = self._from_either(request_data, query_parameters, 'sort')
        direction = self._from_either(request_data, query_parameters, 'direction')
        if sort and type(sort) != str:
            return "Invalid request: 'sort' should be a string"
        if direction and type(direction) != str:
            return "Invalid request: 'direction' should be a string"
        if sort or direction:
            if (sort and not direction) or (direction and not sort):
                return "You must specify 'sort' and 'direction' together in the request - not just one of them"
            if sort not in allowed_sort_columns:
                return f"Invalid request: invalid sort column"
            if sort['direction'].lower() not in ['asc', 'desc']:
                return "Invalid request: direction must be 'asc' or 'desc'"
        return self.check_search_in_request_data(request_data, query_parameters)

    def check_search_in_request_data(self, request_data, query_parameters):
        return None

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
            raise ValueError("{error_prefix} you must provide a model instance in the 'model' configuration setting, but a class was provided instead")
        self._model = self._di.build(configuration['model_class']) if has_model_class else configuration['model']
        self._columns = self._model.columns(overrides=configuration.get('overrides'))
        model_class_name = self._model.__class__.__name__
        # checks for searchable_columns and readable_columns
        self._check_columns_in_configuration(configuration, 'readable_columns')

        if not 'default_sort_column' in configuration:
            raise ValueError(f"{error_prefix} missing required configuration 'default_sort_column'")

        # sortable_columns, wheres, and joins should all be iterables
        for (config_name, contents) in {'sortable_columns': 'column names', 'where': 'conditions', 'join': 'joins'}.items():
            if config_name not in configuration:
                continue
            if not hasattr(configuration[config_name], '__iter__') or type(configuration[config_name]) == str:
                raise ValueError(
                    f"{error_prefix} '{config_name}' should be an iterable of {contents} " +
                    f", not {str(type(configuration[config_name]))}"
                )

        # checks for sortable_columns
        if 'sortable_columns' in configuration:
            for column_name in configuration['sortable_columns']:
                if column_name not in self._columns:
                    raise ValueError(
                        f"{error_prefix} 'sortable_columns' references column named {column_name} " +
                        f"but this column does not exist for model '{model_class_name}'"
                    )

        # common checks for group_by and default_sort_column
        for config_name in ['group_by', 'default_sort_column']:
            if config_name in configuration and configuration[config_name] and configuration[config_name] not in self._columns:
                raise ValueError(
                    f"{error_prefix} '{config_name}' references column named {column_name} " +
                    f"but this column does not exist for model '{model_class_name}'"
                )

        for config_name in ['default_page_length', 'max_page_length']:
            if config_name in configuration and type(configuration[config_name]) != int:
                raise ValueError(
                    f"{error_prefix} '{config_name}' should be an int, not {str(type(configuration[config_name]))}"
                )

    def _check_columns_in_configuration(self, configuration, config_name):
        error_prefix = 'Configuration error for %s:' % (self.__class__.__name__)
        model_class_name = self._model.__class__.__name__
        if not configuration.get(config_name):
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
            if config_name == 'readable_columns' and not self._columns[column_name].is_readable:
                raise ValueError(
                    f"{error_prefix} '{config_name}' references column named {column_name} " +
                    f"but this column does not exist for model '{model_class_name}'"
                )

    def _from_either(self, request_data, query_parameters, key, default=None):
        """
        Returns the key from either object.  Assumes it is not present in both
        """
        return request_data.get(query_parameters.get(key, default))

    def _get_columns(self, column_type):
        resolved_columns = OrderedDict()
        for column_name in self.configuration(f'{column_type}_columns'):
            if column_name not in self._columns:
                class_name = self.__class__.__name__
                model_class = self._model.__class__.__name__
                raise ValueError(
                    f"Handler {class_name} was configured with {column_type} column '{column_name}' but this " +
                    f"column doesn't exist for model {model_class}"
                )
            resolved_columns[column_name] = self._columns[column_name]
        return resolved_columns

    def _get_readable_columns(self):
        if self._readable_columns is None:
            self._readable_columns = self._get_columns('readable')
        return self._readable_columns

    def _get_searchable_columns(self):
        if self._searchable_columns is None:
            self._searchable_columns = self._get_columns('searchable')
        return self._searchable_columns

    def documentation(self, include_search=False):
        nice_model = string.camel_case_to_words(self._model.__class__.__name__)
        schema_model_name = string.camel_case_to_words(self._model.__class__.__name__)
        data_schema = self.documentation_data_schema()

        authentication = self.configuration('authentication')
        standard_error_responses = []
        if not getattr(authentication, 'is_public', False):
            standard_error_responses.append(self.documentation_access_denied_response())
            if getattr(authentication, 'can_authorize', False):
                standard_error_responses.append(self.documentation_unauthorized_response())

        requests = [
            autodoc.request.Request(
                f'Fetch the list of current {nice_model} records',
                [
                    self.documentation_success_response(
                        autodoc.schema.Array('data', autodoc.schema.Object(
                            nice_model,
                            children=data_schema,
                            model_name=schema_model_name
                        )),
                        description=f'The matching {nice_model} records',
                        include_pagination=True,
                    ),
                    *standard_error_responses,
                    self.documentation_generic_error_response(),
                ],
                parameters=[
                    *self.documentation_url_search_parameters(),
                    *self.documentation_pagination_parameters(),
                    *self.documentation_url_sort_parameters(),
                    *self.configuration('authentication').documentation_request_parameters()
                ],
            ),
            autodoc.request.Request(
                'Fetch the details of the ' + nice_model + ' with an id of {id}',
                [
                    self.documentation_success_response(
                        autodoc.schema.Object(
                            'data',
                            children=data_schema,
                            model_name=schema_model_name,
                        ),
                        description=f'The matching {nice_model}'
                    ),
                    *standard_error_responses,
                    self.documentation_not_found(),
                ],
                relative_path='{id}',
                parameters=[
                    *self.configuration('authentication').documentation_request_parameters(),
                    self.documentation_id_url_parameter(),
                ],
            )
        ]

        # figure out what to do with the search endpoint
        if not include_search:
            return requests

        requests.append(autodoc.request.Request(
            f'Advanced options for searching {nice_model} records',
            [
                self.documentation_success_response(
                    autodoc.schema.Array('data', autodoc.schema.Object(
                        nice_model,
                        children=data_schema,
                        model_name=schema_model_name
                    )),
                    description=f'The matching {nice_model} records',
                    include_pagination=True,
                ),
                *standard_error_responses,
                self.documentation_generic_error_response(),
            ],
            relative_path='search',
            request_methods='POST',
            parameters=[
                *self.documentation_json_search_parameters(),
                *self.configuration('authentication').documentation_request_parameters(),
            ],
        ))
        return requests

    def documentation_models(self):
        schema_model_name = string.camel_case_to_snake_case(self._model.__class__.__name__)

        return {
            schema_model_name: autodoc.schema.Object(
                'data',
                children=self.documentation_data_schema(),
            ),
        }

    def documentation_id_url_parameter(self):
        id_column_name = self.id_column_name
        if id_column_name in self._columns:
            id_column_schema = self._columns[id_column_name].documentation()
        else:
            id_column_schema = autodoc.schema.Integer('id')
        return autodoc.request.URLPath(
            id_column_schema,
            description='The id of the record to fetch',
            required=True,
        )

    def documentation_pagination_parameters(self):
        return [
            autodoc.request.URLParameter(
                autodoc.schema.Integer('start'),
                description='The index of the record to start listing results at (0-indexed)'
            ),
            autodoc.request.URLParameter(
                autodoc.schema.Integer('limit'),
                description='The number of records to return'
            ),
        ]

    def documentation_url_sort_parameters(self):
        sort_columns = self.configuration('sortable_columns')
        if not sort_columns:
            sort_columns = list(self._columns.keys())
        directions = ['asc', 'desc']

        return [
            autodoc.request.URLParameter(
                autodoc.schema.Enum('sort', sort_columns, autodoc.schema.String('sort'), example='name'),
                description=f'Column to sort by',
            ),
            autodoc.request.URLParameter(
                autodoc.schema.Enum('direction', directions, autodoc.schema.String('direction'), example='asc'),
                description=f'Direction to sort',
            ),
        ]

    def documentation_url_search_parameters(self):
        return [
            autodoc.request.URLParameter(
                column.documentation(),
                description=f'Search by {column.name} (via exact match)',
            )
            for column in self._get_searchable_columns().values()
        ]

    def documentation_json_search_parameters(self):
        # named 'where' in the request
        where_condition = autodoc.schema.Object(
            'condition',
            [
                autodoc.schema.Enum(
                    'column',
                    [column.name for column in self._get_searchable_columns().values()],
                    autodoc.schema.String('column_name'),
                    example='name',
                ),
                autodoc.schema.Enum(
                    'operator',
                    condition_parser.ConditionParser.operators,
                    autodoc.schema.String('operator'),
                    example='=',
                ),
                autodoc.schema.String('value', example='Jane'),
            ],
        )

        allowed_sort_columns = self.configuration('sortable_columns')
        if not allowed_sort_columns:
            allowed_sort_columns = list(self._columns.keys())

        sort_item = autodoc.schema.Object(
            'sort',
            [
                autodoc.schema.Enum(
                    'column',
                    allowed_sort_columns,
                    autodoc.schema.String('column'),
                    example='name',
                ),
                autodoc.schema.Enum(
                    'direction',
                    ['asc', 'desc'],
                    autodoc.schema.String('direction'),
                    example='asc',
                ),
            ]
        )

        return [
            autodoc.request.JSONBody(
                autodoc.schema.Array('where', where_condition), description='List of search conditions'
            ),
            autodoc.request.JSONBody(
                autodoc.schema.Array('sort', sort_item), description='List of sort directives (max 2)'
            ),
            autodoc.request.JSONBody(
                autodoc.schema.Integer('start', example=0), description='The 0-indexed record to start results from'
            ),
            autodoc.request.JSONBody(
                autodoc.schema.Integer('limit', example=100), description='The number of records to return'
            ),
        ]
