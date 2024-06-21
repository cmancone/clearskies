from .api_backend import ApiBackend
from typing import Any, Dict


class ApiGetOnlyBackend(ApiBackend):
    _requests = None
    _auth = None
    _id_column_name = None

    _allowed_configs = [
        "wheres",
        "table_name",
        "model_columns",
        "select_all",
    ]

    def __init__(self, requests):
        self._requests = requests

    def configure(self, auth=None, origin="", id_column_name="id"):
        self._auth = auth
        self._origin = origin
        self._id_column_name = id_column_name

    def records_url(self, configuration):
        if not len(configuration["wheres"]):
            raise ValueError(
                f"When using the {self.__class__.__name__} backend, you must search the model by the id column.  A records request was executed but no search conditions were found."
            )
        record_id = None
        for where in configuration["wheres"]:
            if where["column"] == self._id_column_name:
                record_id = where["values"][0]
        if not record_id:
            raise ValueError(
                f"When using  the {self.__class__.__name__} backend, you must search by the id column ('{self._id_column_name}').  A records request was executed but there was no condition set for the '{self._id_column_name}' column"
            )

        return self._origin + configuration["table_name"].strip("/") + f"/{record_id}"

    def records_method(self, configuration: Dict[str, Any]) -> str:
        return "GET"

    def _map_records_response(self, json):
        response = super()._map_records_response(json)
        if isinstance(response, dict):
            return [response]
        return response
