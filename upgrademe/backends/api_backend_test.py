import unittest
from unittest.mock import MagicMock, call
from .api_backend import ApiBackend


class ApiBackendTest(unittest.TestCase):
    def setUp(self):
        response = type('', (), {'json': lambda: {"data":[{"id":5}]}})
        self.requests = type('', (), {
            'get': MagicMock(return_value=response),
            'post': MagicMock(return_value={'data': {'my': 'data'}}),
            'patch': MagicMock(return_value={'data': {'my': 'data'}}),
        })()
        self.auth = type('', (), {
            'headers': MagicMock(return_value={'Authorization': 'Bearer: asdfer'}),
        })()
        self.backend = ApiBackend('https://example.com', self.requests, self.auth)

    def test_update(self):
        response = self.backend.update('5', {'hey': 'sup'}, 'model')
        self.requests.patch.assert_called_with(
            'https://example.com',
            headers={'Authorization': 'Bearer: asdfer'},
            json={'hey': 'sup'},
        )
        self.assertEquals({'my': 'data'}, response)

    def test_create(self):
        response = self.backend.create({'hey': 'sup'}, 'model')
        self.requests.post.assert_called_with(
            'https://example.com',
            headers={'Authorization': 'Bearer: asdfer'},
            json={'hey': 'sup'},
        )
        self.assertEquals({'my': 'data'}, response)

    def test_count(self):
        response = type('', (), {'json': lambda: {"total_matches":10}})
        self.requests.get = MagicMock(return_value=response)
        count = self.backend.count({
            'wheres': [
                {'column': 'age', 'operator': '<=', 'values': [10], 'parsed': ''},
                {'column': 'id', 'operator': '=', 'values': [123], 'parsed': ''},
            ],
            'sorts': [{'column': 'age', 'direction': 'desc'}],
            'limit_start': 200,
            'limit_length': 100,
        })
        self.assertEquals(10, count)
        self.requests.get.assert_called_with(
            'https://example.com',
            headers={'Authorization': 'Bearer: asdfer'},
            json={
                'count_only': True,
                'wheres': [
                    {'column': 'age', 'operator': '<=', 'values': [10]},
                    {'column': 'id', 'operator': '=', 'values': [123]},
                ],
                'sorts': [{'column': 'age', 'direction': 'desc'}],
                'start': 200,
                'length': 100,
            }
        )
