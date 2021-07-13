from .backend import Backend


class ApiBackend(Backend):
    url = None
    _requests = None
    _auth = None
    _records = None

    _allowed_configs = [
        'wheres',
        'sorts',
        'limit_start',
        'limit_length',
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
        return [self.url, 'DELETE', {'id': id}, {}]

    def _validate_delete_response(self, json):
        if 'status' not in json:
            raise ValueError("Unexpected response to delete API request")
        return json['status'] == 'success'

    def count(self, configuration, model):
        configuration = self._check_query_configuration(configuration)
        [url, method, json_data, headers] = self._build_count_request(configuration)
        response = self._execute_request(url, method, json=json_data, headers=headers, retry_auth=True)
        return self._map_count_response(response.json())

    def _build_count_request(self, configuration):
        return [
            self.url,
            'GET',
            {**{'count_only': True}, **self._as_post_data(configuration)},
            {}
        ]

    def _map_count_response(self, json):
        if not 'total_matches' in json:
            raise ValueError("Unexpected API response when executing count request")
        return json['total_matches']

    def records(self, configuration, model):
        configuration = self._check_query_configuration(configuration)
        [url, method, json_data, headers] = self._build_records_request(configuration)
        response = self._execute_request(url, method, json=json_data, headers=headers, retry_auth=True)
        return self._map_records_response(response.json())

    def _build_records_request(self, configuration):
        return [self.url, 'GET', self._as_post_data(configuration), {}]

    def _map_records_response(self, json):
        if not 'data' in json:
            raise ValueError("Unexpected response from records request")
        return json['data']

    def _execute_request(self, url, method, json=None, headers=None, retry_auth=False):
        if json is None:
            json = {}
        if headers is None:
            headers = {}

        headers = {**headers, **self._auth.headers(retry_auth=retry_auth)}
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
            if self._auth.has_dynamic_credentials and retry_auth:
                return self._execute_request(url, method, json=json, headers=headers, retry_auth=False)
            response.raise_for_status()

        return response

    def _check_query_configuration(self, configuration):
        for key in configuration.keys():
            if key not in self._allowed_configs and configuration[key]:
                raise KeyError(
                    f"ApiBackend does not support config '{key}'. You may be using the wrong backend"
                )

        for key in self._allowed_configs:
            if not key in configuration:
                configuration[key] = [] if key[-1] == 's' else ''
        return configuration

    def _as_post_data(self, configuration):
        data = {
            'where': list(map(lambda where: self._where_for_post(where), configuration['wheres'])),
            'sort': configuration['sorts'],
            'start': configuration['limit_start'],
            'limit': configuration['limit_length'],
        }
        return {key: value for (key, value) in data.items() if value}

    def _where_for_post(self, where):
        return {
            'column': where['column'],
            'operator': where['operator'],
            'values': where['values'],
        }
