import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, call

from .restful_api_advanced_search_backend import RestfulApiAdvancedSearchBackend


class RestfulApiAdvancedSearchBackendTest(unittest.TestCase):
    def setUp(self):
        self.api_response = {"status": "success", "data": {"id": 5}}
        response = type("", (), {"ok": True, "json": lambda: self.api_response, "content": "sup"})
        self.requests = type(
            "",
            (),
            {
                "request": MagicMock(return_value=response),
            },
        )()
        self.auth = type(
            "",
            (),
            {
                "headers": MagicMock(return_value={"Authorization": "Bearer: asdfer"}),
            },
        )()
        self.backend = RestfulApiAdvancedSearchBackend(self.requests)
        self.backend.configure(auth=self.auth)
        self.model = type(
            "",
            (),
            {
                "id_column_name": "id",
                "table_name": MagicMock(return_value="https://example.com"),
                "columns": MagicMock(return_value={}),
                "data": {},
            },
        )

    def test_update(self):
        response = self.backend.update("5", {"hey": "sup"}, self.model)
        self.requests.request.assert_called_with(
            "PATCH", "https://example.com/5", json={"hey": "sup"}, headers={}, auth=self.auth
        )
        self.assertEqual({"id": 5}, response)

    def test_create(self):
        response = self.backend.create({"hey": "sup"}, self.model)
        self.requests.request.assert_called_with(
            "POST", "https://example.com", json={"hey": "sup"}, headers={}, auth=self.auth
        )
        self.assertEqual({"id": 5}, response)

    def test_delete(self):
        response = self.backend.delete(5, self.model)
        self.requests.request.assert_called_with("DELETE", "https://example.com/5", headers={}, auth=self.auth)

        self.assertEqual(True, response)

    def test_count(self):
        response = type("", (), {"ok": True, "json": lambda: {"total_matches": 10}})
        self.requests.request = MagicMock(return_value=response)
        count = self.backend.count(
            {
                "wheres": [
                    {"column": "age", "operator": "<=", "values": [10], "parsed": ""},
                    {"column": "id", "operator": "=", "values": [123], "parsed": ""},
                ],
                "sorts": [{"column": "age", "direction": "desc"}],
                "pagination": {"start": 200},
                "limit": 100,
                "table_name": self.model.table_name(),
            },
            self.model,
        )
        self.assertEqual(10, count)
        self.requests.request.assert_called_with(
            "POST",
            "https://example.com/search",
            json={
                "count_only": True,
                "where": [
                    {"column": "age", "operator": "<=", "value": 10},
                    {"column": "id", "operator": "=", "value": 123},
                ],
                "sort": [{"column": "age", "direction": "desc"}],
                "start": 200,
                "limit": 100,
            },
            headers={},
            auth=self.auth,
        )

    def test_query(self):
        response = type("", (), {"ok": True, "json": lambda: {"data": [{"id": 5}, {"id": 10}]}})
        self.requests.request = MagicMock(return_value=response)
        records = self.backend.records(
            {
                "wheres": [
                    {"column": "age", "operator": "<=", "values": [10], "parsed": ""},
                    {"column": "id", "operator": "=", "values": [123], "parsed": ""},
                ],
                "sorts": [{"column": "age", "direction": "desc"}],
                "pagination": {"start": 200},
                "limit": 100,
                "table_name": self.model.table_name(),
            },
            self.model,
        )
        self.requests.request.assert_called_with(
            "POST",
            "https://example.com/search",
            json={
                "where": [
                    {"column": "age", "operator": "<=", "value": 10},
                    {"column": "id", "operator": "=", "value": 123},
                ],
                "sort": [{"column": "age", "direction": "desc"}],
                "start": 200,
                "limit": 100,
            },
            headers={},
            auth=self.auth,
        )

        self.assertEqual({"id": 5}, records[0])
        self.assertEqual({"id": 10}, records[1])

    def test_query_empty(self):
        response = type("", (), {"ok": True, "json": lambda: {"data": [{"id": 5}, {"id": 10}]}})
        self.requests.request = MagicMock(return_value=response)
        records = self.backend.records(
            {
                "wheres": [],
                "sorts": [],
                "pagination": {"start": 0},
                "limit": 0,
                "table_name": self.model.table_name(),
            },
            self.model,
        )
        self.requests.request.assert_called_with("POST", "https://example.com/search", headers={}, auth=self.auth)

        self.assertEqual({"id": 5}, records[0])
        self.assertEqual({"id": 10}, records[1])
