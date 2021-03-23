from .backend import Backend


class ApiBackend(Backend):
    url = None
    _requests = None
    _auth = None
    _records = None
    _iterator_index = None

    _allowed_configs = [
        'wheres',
        'sorts',
        'limit_start',
        'limit_length',
        'table_name',
    ]

    _empty_configs = [
        'group_by_column',
        'selects',
        'joins',
    ]

    def __init__(self, url, requests, auth):
        self.url = url
        self._requests = requests
        self._auth = auth

    def configure(self):
        pass

    def update(self, id, data, model):
        response = self._requests.patch(
            self.url,
            headers=self._auth.headers(),
            json=data,
        )

        return response.json()['data']

    def create(self, data, model):
        response = self._requests.post(
            self.url,
            headers=self._auth.headers(),
            json=data,
        )

        return response.json()['data']

    def delete(self, id, model):
        response = self._requests.delete(
            self.url,
            headers=self._auth.headers(),
            json={'id': id}
        )

        return response.json()['status'] == 'success'

    def count(self, configuration):
        configuration = self._check_query_configuration(configuration)
        response = self._requests.get(
            self.url,
            headers=self._auth.headers(),
            json={
                **{'count_only': True},
                **self._as_post_data(configuration),
            }
        )
        return response.json()['total_matches']

    def iterator(self, configuration):
        configuration = self._check_query_configuration(configuration)
        response = self._requests.get(
            self.url,
            headers=self._auth.headers(),
            json=self._as_post_data(configuration),
        )
        self._records = response.json()['data']
        self._iterator_index = -1
        return self

    def next(self):
        if self._records is None:
            raise ValueError("Must call iterator before calling next")

        self._iterator_index += 1
        if self._iterator_index >= len(self._records):
            raise StopIteration
        return self._records[self._iterator_index]

    def _check_query_configuration(self, configuration):
        for key in configuration.keys():
            if key not in self._allowed_configs:
                raise KeyError(
                    f"CursorBackend does not support config '{key}'. You may be using the wrong backend"
                )

        for key in self._allowed_configs:
            if not key in configuration:
                configuration[key] = [] if key[-1] == 's' else ''
        return configuration

    def _as_post_data(self, configuration):
        return {
            'where': list(map(lambda where: self._where_for_post(where), configuration['wheres'])),
            'sort': configuration['sorts'],
            'start': configuration['limit_start'],
            'limit': configuration['limit_length'],
        }

    def _where_for_post(self, where):
        return {
            'column': where['column'],
            'operator': where['operator'],
            'values': where['values'],
        }
