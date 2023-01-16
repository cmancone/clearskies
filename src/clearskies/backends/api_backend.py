from .backend import Backend
from typing import Any, Callable, Dict, List, Tuple
from ..autodoc.schema import Integer as AutoDocInteger
from .. import model
from ..column_types import JSON, DateTime
class ApiBackend(Backend):
    url = None
    _requests = None
    _auth = None
    _records = None

    _allowed_configs = [
        'select_all',
        'wheres',
        'sorts',
        'limit',
        'pagination',
        'table_name',
        'model_columns',
    ]

    _empty_configs = [
        'group_by_column',
        'selects',
        'joins',
    ]

    def __init__(self, requests):
        self._requests = requests

    def configure(self, url=None, auth=None):
        self.url = url
        self._auth = auth

    def update(self, id, data, model):
        [url, method, json_data, headers] = self._build_update_request(id, data, model)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        if not response.content:
            return {**model.data, **data}
        return self._map_update_response(response.json())

    def _build_update_request(self, id, data, model):
        return [self.url, 'PATCH', data, {}]

    def _map_update_response(self, json):
        if not 'data' in json:
            raise ValueError("Unexpected API response to update request")
        return json['data']

    def create(self, data, model):
        [url, method, json_data, headers] = self._build_create_request(data, model)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        return self._map_create_response(response.json())

    def _build_create_request(self, data, model):
        return [self.url, 'POST', data, {}]

    def _map_create_response(self, json):
        if not 'data' in json:
            raise ValueError("Unexpected API response to create request")
        return json['data']

    def delete(self, id, model):
        [url, method, json_data, headers] = self._build_delete_request(id, model)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        return self._validate_delete_response(response.json())

    def _build_delete_request(self, id, model):
        return [self.url, 'DELETE', {model.id_column_name: id}, {}]

    def _validate_delete_response(self, json):
        if 'status' not in json:
            raise ValueError("Unexpected response to delete API request")
        return json['status'] == 'success'

    def count(self, configuration, model):
        configuration = self._check_query_configuration(configuration)
        [url, method, json_data, headers] = self._build_count_request(configuration)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        return self._map_count_response(response.json())

    def _build_count_request(self, configuration):
        return [self.url, 'GET', {**{'count_only': True}, **self._as_post_data(configuration)}, {}]

    def _map_count_response(self, json):
        if not 'total_matches' in json:
            raise ValueError("Unexpected API response when executing count request")
        return json['total_matches']

    def records(self, configuration, model, next_page_data=None):
        configuration = self._check_query_configuration(configuration)
        [url, method, json_data, headers] = self._build_records_request(configuration)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        records = self._map_records_response(response.json())
        if type(next_page_data) == dict:
            limit = configuration.get('limit', None)
            start = configuration.get('pagination', {}).get('start', 0)
            if limit and len(records) == limit:
                next_page_data['start'] = start + limit
        return records

    def _build_records_request(self, configuration):
        return [self.url, 'GET', self._as_post_data(configuration), {}]

    def _map_records_response(self, json):
        if not 'data' in json:
            raise ValueError("Unexpected response from records request")
        return json['data']

    def _execute_request(self, url, method, json=None, headers=None, is_retry=False):
        if json is None:
            json = {}
        if headers is None:
            headers = {}

        headers = {**headers, **self._auth.headers(retry_auth=is_retry)}
        # the requests library seems to build a slightly different request if you specify the json parameter,
        # even if it is null, and this causes trouble for some picky servers
        if not json:
            response = self._requests.request(
                method,
                url,
                headers=headers,
            )
        else:
            response = self._requests.request(
                method,
                url,
                headers=headers,
                json=json,
            )

        if not response.ok:
            if self._auth.has_dynamic_credentials and not is_retry:
                return self._execute_request(url, method, json=json, headers=headers, is_retry=True)
            if not response.ok:
                raise ValueError(f'Failed request.  Status code: {response.status_code}, message: {response.content}')

        return response

    def _check_query_configuration(self, configuration):
        for key in configuration.keys():
            if key not in self._allowed_configs and configuration[key]:
                raise KeyError(f"ApiBackend does not support config '{key}'. You may be using the wrong backend")

        for key in self._allowed_configs:
            if not key in configuration:
                configuration[key] = [] if key[-1] == 's' else ''
        return configuration

    def _as_post_data(self, configuration):
        data = {
            'where': list(map(lambda where: self._where_for_post(where), configuration['wheres'])),
            'sort': configuration['sorts'],
            'start': configuration['pagination'].get('start', 0),
            'limit': configuration['limit'],
        }
        return {key: value for (key, value) in data.items() if value}

    def _where_for_post(self, where):
        return {
            'column': where['column'],
            'operator': where['operator'],
            'values': where['values'],
        }

    def validate_pagination_kwargs(self, kwargs: Dict[str, Any], case_mapping: Callable) -> str:
        extra_keys = set(kwargs.keys()) - set(self.allowed_pagination_keys())
        if len(extra_keys):
            key_name = case_mapping('start')
            return "Invalid pagination key(s): '" + "','".join(extra_keys) + f"'.  Only '{key_name}' is allowed"
        if 'start' not in kwargs:
            key_name = case_mapping('start')
            return f"You must specify '{key_name}' when setting pagination"
        start = kwargs['start']
        try:
            start = int(start)
        except:
            key_name = case_mapping('start')
            return f"Invalid pagination data: '{key_name}' must be a number"
        return ''

    def allowed_pagination_keys(self) -> List[str]:
        return ['start']

    def documentation_pagination_next_page_response(self, case_mapping: Callable) -> List[Any]:
        return [AutoDocInteger(case_mapping('start'), example=10)]

    def documentation_pagination_next_page_example(self, case_mapping: Callable) -> Dict[str, Any]:
        return {case_mapping('start'): 10}

    def documentation_pagination_parameters(self, case_mapping: Callable) -> List[Tuple[Any, Any]]:
        return [(
            AutoDocInteger(case_mapping('start'),
                           example=10), 'The zero-indexed record number to start listing results from'
        )]

    def column_from_backend(self, column, value):
        """
        We have a couple columns we want to override transformations for
        """
        # most importantly, there's no need to transform a JSON column in either direction
        if isinstance(column, JSON):
            return value
        return super().column_from_backend(column, value)

    def column_to_backend(self, column, backend_data):
        """
        We have a couple columns we want to override transformations for
        """
        # most importantly, there's no need to transform a JSON column in either direction
        if isinstance(column, JSON):
            return backend_data
        # also, APIs tend to have a different format for dates than SQL
        if isinstance(column, DateTime):
            return {**backend_data, **{column.name: backend_data[column.name].isoformat()}}
        return column.to_backend(backend_data)
