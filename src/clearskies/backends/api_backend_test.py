import unittest
from unittest.mock import MagicMock, call
from .api_backend import ApiBackend


class ApiBackendTest(unittest.TestCase):
    def setUp(self):
        self.api_response = {"status": "success", "data": {"id": 5}}
        response = type('', (), {'json': lambda: self.api_response})
        self.requests = type('', (), {
            'get': MagicMock(return_value=response),
            'post': MagicMock(return_value=response),
            'patch': MagicMock(return_value=response),
            'delete': MagicMock(return_value=response),
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
        self.assertEquals({"id": 5}, response)

    def test_create(self):
        response = self.backend.create({'hey': 'sup'}, 'model')
        self.requests.post.assert_called_with(
            'https://example.com',
            headers={'Authorization': 'Bearer: asdfer'},
            json={'hey': 'sup'},
        )
        self.assertEquals({"id": 5}, response)

    def test_delete(self):
        response = self.backend.delete(5, 'model')
        self.requests.delete.assert_called_with(
            'https://example.com',
            headers={'Authorization': 'Bearer: asdfer'},
            json={'id': 5},
        )

        self.assertEquals(True, response)

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
                'where': [
                    {'column': 'age', 'operator': '<=', 'values': [10]},
                    {'column': 'id', 'operator': '=', 'values': [123]},
                ],
                'sort': [{'column': 'age', 'direction': 'desc'}],
                'start': 200,
                'limit': 100,
            }
        )

    def test_query(self):
        response = type('', (), {'json': lambda: {"data":[{"id": 5}, {"id": 10}]}})
        self.requests.get = MagicMock(return_value=response)
        iterator = self.backend.iterator({
            'wheres': [
                {'column': 'age', 'operator': '<=', 'values': [10], 'parsed': ''},
                {'column': 'id', 'operator': '=', 'values': [123], 'parsed': ''},
            ],
            'sorts': [{'column': 'age', 'direction': 'desc'}],
            'limit_start': 200,
            'limit_length': 100,
        })
        self.requests.get.assert_called_with(
            'https://example.com',
            headers={'Authorization': 'Bearer: asdfer'},
            json={
                'where': [
                    {'column': 'age', 'operator': '<=', 'values': [10]},
                    {'column': 'id', 'operator': '=', 'values': [123]},
                ],
                'sort': [{'column': 'age', 'direction': 'desc'}],
                'start': 200,
                'limit': 100,
            }
        )

        self.assertEquals({"id": 5}, iterator.next())
        self.assertEquals({"id": 10}, iterator.next())
        self.assertRaises(StopIteration, iterator.next)
