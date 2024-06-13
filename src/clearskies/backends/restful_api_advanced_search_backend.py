from .api_backend import ApiBackend
from typing import Any, Callable, Dict, List, Tuple
from .. import model
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

    def records_url(self, configuration: Dict[str, Any]) -> str:
        return configuration["table_name"].rstrip("/") + "/search"

    def delete_url(self, id: str, model: model.Model) -> str:
        table_name = model.table_name().rstrip("/")
        return f"{table_name}/{id}"

    def update_url(self, id: str, model: model.Model) -> str:
        table_name = model.table_name().rstrip("/")
        return f"{table_name}/{id}"

    def create_url(self, data: Dict[str, Any], model: model.Model) -> str:
        return model.table_name().rstrip("/")

    def records_method(self, configuration: Dict[str, Any]) -> str:
        return "POST"

    def count_method(self, configuration: Dict[str, Any]) -> str:
        return "POST"

    def _build_delete_request(self, id, model):
        data = model.data
        (url, data) = self._finalize_url_and_data(self.delete_url(id, model), data)
        return [url, self.delete_method(id, model), {}, {}]

    def _build_count_request(self, configuration):
        [url, method, json_data, headers] = super()._build_count_request(configuration)
        json_data["count_only"] = True
        return [url, method, json_data, headers]

    def records(self, configuration, model, next_page_data={}):
        configuration = self._check_query_configuration(configuration)
        [url, method, json_data, headers] = self._build_records_request(configuration)
        response = self._execute_request(url, method, json=json_data, headers=headers).json()
        records = self._map_records_response(response)
        for next_page_key in ["nextPage", "NextPage", "next_page"]:
            if response.get("pagination", {}).get(next_page_key):
                for key, value in response["pagination"][next_page_key].items():
                    next_page_data[key] = value
        return records

    def _as_post_data(self, configuration):
        data = {
            "where": list(
                map(lambda where: self._where_for_post(where, configuration["model_columns"]), configuration["wheres"])
            ),
            "sort": configuration["sorts"],
            "start": configuration["pagination"].get("start", 0),
            "limit": configuration["limit"],
        }
        return {key: value for (key, value) in data.items() if value}

    def _where_for_post(self, where, columns):
        prefix = ""
        if where.get("table"):
            prefix = where["table"] + "."
        return {
            "column": prefix + where["column"],
            "operator": where["operator"],
            "value": self.normalize_outgoing_value(where, columns, where["values"][0]),
        }

    def normalize_outgoing_value(self, where, columns, value):
        column_name = where["column"]
        if where.get("table") or column_name not in columns:
            return value
        normalized_data = self.column_to_backend(columns[column_name], {column_name: value})
        if column_name in normalized_data:
            return normalized_data[column_name]
        return value
