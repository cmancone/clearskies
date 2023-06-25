from .api_backend import ApiBackend
from typing import Any, Callable, Dict, List, Tuple
from ..autodoc.schema import Integer as AutoDocInteger


class RestfulApiAdvancedSearchBackend(ApiBackend):
    _requests = None
    _auth = None
    _records = None

    _allowed_configs = [
        "wheres",
        "sorts",
        "limit",
        "pagination",
        "table_name",
        "model_columns",
        "select_all",
    ]

    _empty_configs = [
        "group_by_column",
        "selects",
        "joins",
    ]

    def __init__(self, requests):
        self._requests = requests

    def configure(self, auth=None):
        self._auth = auth

    def update(self, id, data, model):
        [url, method, json_data, headers] = self._build_update_request(id, data, model)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        if not response.content:
            return {**model.data, **data}
        return self._map_update_response(response.json())

    def _build_update_request(self, id, data, model):
        url = model.table_name().rstrip("/")
        return [f"{url}/{id}", "PATCH", data, {}]

    def _map_update_response(self, json):
        if not "data" in json:
            raise ValueError("Unexpected API response to update request")
        return json["data"]

    def create(self, data, model):
        [url, method, json_data, headers] = self._build_create_request(data, model)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        return self._map_create_response(response.json())

    def _build_create_request(self, data, model):
        return [model.table_name().rstrip("/"), "POST", data, {}]

    def _map_create_response(self, json):
        if not "data" in json:
            raise ValueError("Unexpected API response to create request")
        return json["data"]

    def delete(self, id, model):
        [url, method, json_data, headers] = self._build_delete_request(id, model)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        return self._validate_delete_response(response.json())

    def _build_delete_request(self, id, model):
        url = model.table_name().rstrip("/")
        return [f"{url}/{id}", "DELETE", {}, {}]

    def _validate_delete_response(self, json):
        if "status" not in json:
            raise ValueError("Unexpected response to delete API request")
        return json["status"] == "success"

    def count(self, configuration, model):
        configuration = self._check_query_configuration(configuration)
        [url, method, json_data, headers] = self._build_count_request(configuration, model)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        return self._map_count_response(response.json())

    def _build_count_request(self, configuration, model):
        url = model.table_name().rstrip("/") + "/search"
        return [url, "POST", {**{"count_only": True}, **self._as_post_data(configuration, model)}, {}]

    def _map_count_response(self, json):
        if not "total_matches" in json:
            raise ValueError("Unexpected API response when executing count request")
        return json["total_matches"]

    def records(self, configuration, model, next_page_data={}):
        configuration = self._check_query_configuration(configuration)
        [url, method, json_data, headers] = self._build_records_request(configuration, model)
        response = self._execute_request(url, method, json=json_data, headers=headers).json()
        records = self._map_records_response(response)
        for next_page_key in ["nextPage", "NextPage", "next_page"]:
            if response.get("pagination", {}).get(next_page_key):
                for key, value in response["pagination"][next_page_key].items():
                    next_page_data[key] = value
        return records

    def _build_records_request(self, configuration, model):
        url = model.table_name().rstrip("/") + "/search"
        return [url, "POST", self._as_post_data(configuration, model), {}]

    def _map_records_response(self, json):
        if not "data" in json:
            raise ValueError("Unexpected response from records request")
        return json["data"]

    def _as_post_data(self, configuration, model):
        data = {
            "where": list(map(lambda where: self._where_for_post(where, model), configuration["wheres"])),
            "sort": configuration["sorts"],
            "start": configuration["pagination"].get("start", 0),
            "limit": configuration["limit"],
        }
        return {key: value for (key, value) in data.items() if value}

    def _where_for_post(self, where, model):
        prefix = ""
        if where.get("table"):
            prefix = where["table"] + "."
        return {
            "column": prefix + where["column"],
            "operator": where["operator"],
            "value": self.normalize_outgoing_value(where, model, where["values"][0]),
        }

    def normalize_outgoing_value(self, where, model, value):
        column_name = where["column"]
        columns = model.columns()
        if where.get("table") or column_name not in columns:
            return value
        normalized_data = self.column_to_backend(columns[column_name], {column_name: value})
        if column_name in normalized_data:
            return normalized_data[column_name]
        return value
