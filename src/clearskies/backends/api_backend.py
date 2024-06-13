from .backend import Backend
from typing import Any, Callable, Dict, List, Tuple
from ..autodoc.schema import Integer as AutoDocInteger
from .. import model
from ..column_types import JSON, DateTime
import re


class ApiBackend(Backend):
    url = None
    _requests = None
    _auth = None
    _records = None

    _allowed_configs = [
        "select_all",
        "wheres",
        "sorts",
        "limit",
        "pagination",
        "table_name",
        "model_columns",
    ]

    _empty_configs = [
        "group_by_column",
        "selects",
        "joins",
    ]

    def __init__(self, requests):
        self._requests = requests

    def configure(self, url=None, auth=None):
        self.url = url
        self._auth = auth

    def records_url(self, configuration: Dict[str, Any]) -> str:
        return self.url

    def count_url(self, configuration: Dict[str, Any]) -> str:
        return self.records_url(configuration)

    def delete_url(self, id: str, model: model.Model) -> str:
        return self.url

    def update_url(self, id: str, model: model.Model) -> str:
        return self.url

    def create_url(self, data: Dict[str, Any], model: model.Model) -> str:
        return self.url

    def records_method(self, configuration: Dict[str, Any]) -> str:
        return "GET"

    def count_method(self, configuration: Dict[str, Any]) -> str:
        return "GET"

    def delete_method(self, id: str, model: model.Model) -> str:
        return "DELETE"

    def update_method(self, id: str, model: model.Model) -> str:
        return "PATCH"

    def create_method(self, data: Dict[str, Any], model: model.Model) -> str:
        return "POST"

    def update(self, id, data, model):
        [url, method, json_data, headers] = self._build_update_request(id, data, model)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        if not response.content:
            return {**model.data, **data}
        return self._map_update_response(response.json())

    def _build_update_request(self, id, data, model):
        (url, data) = self._finalize_url_and_data(self.update_url(id, model), data)
        return [url, self.update_method(id, model), data, {}]

    def _map_update_response(self, json):
        if not "data" in json:
            raise ValueError("Unexpected API response to update request")
        return json["data"]

    def create(self, data, model):
        [url, method, json_data, headers] = self._build_create_request(data, model)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        return self._map_create_response(response.json())

    def _build_create_request(self, data, model):
        (url, data) = self._finalize_url_and_data(self.create_url(data, model), data)
        return [url, self.create_method(data, model), data, {}]

    def _map_create_response(self, json):
        if not "data" in json:
            raise ValueError("Unexpected API response to create request")
        return json["data"]

    def delete(self, id, model):
        [url, method, json_data, headers] = self._build_delete_request(id, model)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        return self._validate_delete_response(response.json())

    def _build_delete_request(self, id, model):
        data = model.data
        (url, data) = self._finalize_url_and_data(self.delete_url(id, model), data)
        return [url, self.delete_method(id, model), {model.id_column_name: id}, {}]

    def _validate_delete_response(self, json):
        if "status" not in json:
            raise ValueError("Unexpected response to delete API request")
        return json["status"] == "success"

    def count(self, configuration, model):
        configuration = self._check_query_configuration(configuration)
        [url, method, json_data, headers] = self._build_count_request(configuration)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        return self._map_count_response(response.json())

    def _build_count_request(self, configuration):
        (url, configuration) = self._finalize_url_and_configuration(self.count_url(configuration), configuration)
        return [
            url,
            self.count_method(configuration),
            {**{"count_only": True}, **self._as_post_data(configuration)},
            {},
        ]

    def _map_count_response(self, json):
        if not "total_matches" in json:
            raise ValueError("Unexpected API response when executing count request")
        return json["total_matches"]

    def records(self, configuration, model, next_page_data=None):
        configuration = self._check_query_configuration(configuration)
        [url, method, json_data, headers] = self._build_records_request(configuration)
        response = self._execute_request(url, method, json=json_data, headers=headers)
        records = self._map_records_response(response.json())
        if type(next_page_data) == dict:
            limit = configuration.get("limit", None)
            start = configuration.get("pagination", {}).get("start", 0)
            if limit and len(records) == limit:
                next_page_data["start"] = start + limit
        return records

    def _build_records_request(self, configuration):
        (url, configuration) = self._finalize_url_and_configuration(self.records_url(configuration), configuration)
        return [url, self.records_method(configuration), self._as_post_data(configuration), {}]

    def _map_records_response(self, json):
        if not "data" in json:
            raise ValueError("Unexpected response from records request")
        return json["data"]

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
                raise ValueError(f"Failed request.  Status code: {response.status_code}, message: {response.content}")

        return response

    def _check_query_configuration(self, configuration):
        for key in configuration.keys():
            if key not in self._allowed_configs and configuration[key]:
                raise KeyError(f"ApiBackend does not support config '{key}'. You may be using the wrong backend")

        for key in self._allowed_configs:
            if not key in configuration:
                configuration[key] = [] if key[-1] == "s" else ""
        return configuration

    def _as_post_data(self, configuration):
        data = {
            "where": list(map(lambda where: self._where_for_post(where), configuration["wheres"])),
            "sort": configuration["sorts"],
            "start": configuration["pagination"].get("start", 0),
            "limit": configuration["limit"],
        }
        return {key: value for (key, value) in data.items() if value}

    def _where_for_post(self, where):
        return {
            "column": where["column"],
            "operator": where["operator"],
            "values": where["values"],
        }

    def validate_pagination_kwargs(self, kwargs: Dict[str, Any], case_mapping: Callable) -> str:
        extra_keys = set(kwargs.keys()) - set(self.allowed_pagination_keys())
        if len(extra_keys):
            key_name = case_mapping("start")
            return "Invalid pagination key(s): '" + "','".join(extra_keys) + f"'.  Only '{key_name}' is allowed"
        if "start" not in kwargs:
            key_name = case_mapping("start")
            return f"You must specify '{key_name}' when setting pagination"
        start = kwargs["start"]
        try:
            start = int(start)
        except:
            key_name = case_mapping("start")
            return f"Invalid pagination data: '{key_name}' must be a number"
        return ""

    def allowed_pagination_keys(self) -> List[str]:
        return ["start"]

    def documentation_pagination_next_page_response(self, case_mapping: Callable) -> List[Any]:
        return [AutoDocInteger(case_mapping("start"), example=0)]

    def documentation_pagination_next_page_example(self, case_mapping: Callable) -> Dict[str, Any]:
        return {case_mapping("start"): 0}

    def documentation_pagination_parameters(self, case_mapping: Callable) -> List[Tuple[Any]]:
        return [
            (
                AutoDocInteger(case_mapping("start"), example=0),
                "The zero-indexed record number to start listing results from",
            )
        ]

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
            as_date = (
                backend_data[column.name].isoformat()
                if type(backend_data[column.name]) != str
                else backend_data[column.name]
            )
            return {**backend_data, **{column.name: as_date}}
        return column.to_backend(backend_data)

    def _finalize_url_and_data(self, url: str, data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        (url, used_columns) = self._finalize_url(url, data, model)
        for used_column in used_columns:
            del data[used_column]
        return (url, data)

    def _finalize_url_and_configuration(self, url: str, configuration: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        # we need to convert the wheres in the configuration to a dictionary of key/values, but
        # *only* for cases where we have performed an equals search.
        filters_by_equals = {}
        index_lookup = {}
        for index, where in enumerate(configuration["wheres"]):
            if where["operator"] != "=":
                continue
            filters_by_equals[where["column"]] = where["values"][0]
            index_lookup[where["column"]] = index

        # always call _finalize_url, even if we don't have any search columns,
        # because if there are placeholders in the URL but we don't have any values,
        # then we need to throw an exception.
        (url, used_columns) = self._finalize_url(url, filters_by_equals, model)
        # we need to remove the used entries from the wheres but in doing so we start at the end
        # of the array so our indexes stay valid.
        to_delete = [index_lookup[used_column] for used_column in used_columns]
        to_delete.sort(reverse=True)
        for index_to_delete in to_delete:
            del configuration["wheres"][index_to_delete]

        return (url, configuration)

    def _finalize_url(self, url: str, data: Dict[str, Any], model: model.Models) -> Tuple[str, List[str]]:
        """
        This function is what gives support for placeholders in URLs.  We support two formats:

         1. /some/path/{some_field}/blah
         2. /some/path/:some_field/blah

        The url comes from the `my_url` function, which (by default) is just self.url.  You can
        always extend `my_url` to pull the URL from something else (the `model.table_name()` for instance).

        You would then:

        ```
        models.where("some_field=some_value")
        ```

        and when the API backend makes the call it will then build the appropriate URL.  Naturally,
        you'll want to add a corresponding column to your model, otherwise the model will complain
        that "some_field is not an allowed column in model class 'BLAH'" (since all search columns
        used in a `where` query go through strict input validation).
        """
        # many Snyk API calls require a resource id in the URL.  Let's check if that is the case here,
        # and if so, get  it out of the query configuration
        used_columns = []
        resource_references = self._find_resource_references_in_url(url)
        for resource_reference in resource_references:
            resource_name = resource_reference["name"]
            placeholder = resource_reference["placeholder"]
            if not data.get(resource_name):
                raise ValueError(
                    f"Error building a request with {self.__class__.__name__}: my url, '{url}', has a URL resource named '{resource_name}' but a request was made without providing a value for this resource.  All URL parameters are implicitly required.  Also note that only where clauses with an 'equals' operator will be used when providing search terms for the URL.  So, make sure you add an appropriate: `models.where('{resource_name}=some_value')` search when using the corresponding models class.  Alternatively, if executing a create/delete/update operation, make sure the model and/or save has a value for this column"
                )

            url = url.replace(placeholder, str(data.get(resource_name)))
            used_columns.append(resource_name)
        return (url, used_columns)

    def _find_resource_references_in_url(self, url: str) -> list[str]:
        if not url:
            return []
        # To help with the regexp matching, it helps if the URL both starts and ends with a "/".
        # We don't need to modify the URL at all - we just need it for our matching, so it's fine
        # that our changes aren't propogated back to the calling function.
        if url[-1] != "/":
            url += "/"
        if url[0] != "/":
            url = f"/{url}"
        return [
            *[{"name": reference, "placeholder": "{" + reference + "}"} for reference in re.findall(r"{(\w+)}", url)],
            *[{"name": reference, "placeholder": f":{reference}"} for reference in re.findall(r"/:([^/]+)/", url)],
        ]
