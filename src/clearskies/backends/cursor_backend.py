from .backend import Backend
from typing import Any, Callable, Dict, List, Tuple
from ..autodoc.schema import Integer as AutoDocInteger
from .. import model


class CursorBackend(Backend):
    supports_n_plus_one = True
    _cursor = None

    _allowed_configs = [
        "table_name",
        "wheres",
        "sorts",
        "group_by_column",
        "limit",
        "pagination",
        "selects",
        "select_all",
        "joins",
        "model_columns",
    ]

    _required_configs = [
        "table_name",
    ]

    def __init__(self, cursor):
        self._cursor = cursor
        from .. import ConditionParser

        self.condition_parser = ConditionParser()

    def _table_escape_character(self) -> str:
        """Return the character to use to escape table names in queries."""
        return "`"

    def _column_escape_character(self) -> str:
        """Return the character to use to escape column names in queries."""
        return "`"

    def configure(self):
        pass

    def _finalize_table_name(self, table_name):
        escape = self._table_escape_character()
        if "." not in table_name:
            return f"{escape}{table_name}{escape}"
        return escape + f"{escape}.{escape}".join(table_name.split(".")) + escape

    def update(self, id, data, model):
        query_parts = []
        parameters = []
        escape = self._column_escape_character()
        for key, val in data.items():
            query_parts.append(f"{escape}{key}{escape}=%s")
            parameters.append(val)
        updates = ", ".join(query_parts)

        table_name = self._finalize_table_name(model.table_name())
        self._cursor.execute(
            f"UPDATE {table_name} SET {updates} WHERE {model.id_column_name}=%s", tuple([*parameters, id])
        )

        results = self.records(
            {
                "table_name": model.table_name(),
                "select_all": True,
                "wheres": [
                    {
                        "column": model.id_column_name,
                        "operator": "=",
                        "parsed": f"{model.id_column_name}=%s",
                        "values": [id],
                    }
                ],
            },
            model,
        )
        return results[0]

    def create(self, data, model):
        escape = self._column_escape_character()
        columns = escape + f"{escape}, {escape}".join(data.keys()) + escape
        placeholders = ", ".join(["%s" for i in range(len(data))])

        table_name = self._finalize_table_name(model.table_name())
        self._cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", tuple(data.values()))
        new_id = data.get(model.id_column_name)
        if not new_id:
            new_id = self._cursor.lastrowid
        if not new_id:
            raise ValueError("I can't figure out what the id is for a newly created record :(")

        results = self.records(
            {
                "table_name": model.table_name(),
                "select_all": True,
                "wheres": [
                    {
                        "column": model.id_column_name,
                        "operator": "=",
                        "parsed": f"{model.id_column_name}=%s",
                        "values": [new_id],
                    }
                ],
            },
            model,
        )
        return results[0]

    def delete(self, id, model):
        table_name = self._finalize_table_name(model.table_name())
        self._cursor.execute(f"DELETE FROM {table_name} WHERE {model.id_column_name}=%s", (id,))
        return True

    def count(self, configuration, model):
        configuration = self._check_query_configuration(configuration)
        [query, parameters] = self.as_count_sql(configuration)
        self._cursor.execute(query, tuple(parameters))
        for row in self._cursor:
            return row[0] if type(row) == tuple else row["count"]
        return 0

    def records(
        self, configuration: Dict[str, Any], model: model.Model, next_page_data: Dict[str, str] = None
    ) -> List[Dict[str, Any]]:
        # I was going to get fancy and have this return an iterator, but since I'm going to load up
        # everything into a list anyway, I may as well just return the list, right?
        configuration = self._check_query_configuration(configuration)
        [query, parameters] = self.as_sql(configuration)
        self._cursor.execute(query, tuple(parameters))
        records = [row for row in self._cursor]
        if type(next_page_data) == dict:
            limit = configuration.get("limit", None)
            start = configuration.get("pagination", {}).get("start", 0)
            if limit and len(records) == limit:
                next_page_data["start"] = int(start) + int(limit)
        return records

    def group_by_clause(self, group_by):
        if not group_by:
            return ""
        escape = self._column_escape_character()
        if "." not in group_by:
            return f" GROUP BY {escape}{group_by}{escape}"
        parts = group_by.split(".", 1)
        table = parts[0]
        column = parts[1]
        return f" GROUP BY {escape}{table}{escape}.{escape}{column}{escape}"

    def as_sql(self, configuration):
        escape = self._column_escape_character()
        [wheres, parameters] = self._conditions_as_wheres_and_parameters(
            configuration["wheres"], configuration["table_name"]
        )
        select_parts = []
        if configuration["select_all"]:
            select_parts.append(self._finalize_table_name(configuration["table_name"]) + ".*")
        if configuration["selects"]:
            select_parts.extend(configuration["selects"])
        select = ", ".join(select_parts)
        if configuration["joins"]:
            joins = " " + " ".join([join["raw"] for join in configuration["joins"]])
        else:
            joins = ""
        if configuration["sorts"]:
            sort_parts = []
            for sort in configuration["sorts"]:
                table_name = sort.get("table")
                column_name = sort["column"]
                direction = sort["direction"]
                prefix = self._finalize_table_name(table_name) + "." if table_name else ""
                sort_parts.append(f"{prefix}{escape}{column_name}{escape} {direction}")
            order_by = " ORDER BY " + ", ".join(sort_parts)
        else:
            order_by = ""
        group_by = self.group_by_clause(configuration["group_by_column"])
        limit = ""
        if configuration["limit"]:
            start = 0
            if configuration["pagination"].get("start"):
                start = int(configuration["pagination"]["start"])
            limit = f' LIMIT {start}, {configuration["limit"]}'

        table_name = self._finalize_table_name(configuration["table_name"])
        return [
            f"SELECT {select} FROM {table_name}{joins}{wheres}{group_by}{order_by}{limit}".strip(),
            parameters,
        ]

    def as_count_sql(self, configuration):
        escape = self._column_escape_character()
        # note that this won't work if we start including a HAVING clause
        [wheres, parameters] = self._conditions_as_wheres_and_parameters(
            configuration["wheres"], configuration["table_name"]
        )
        # we also don't currently support parameters in the join clause - I'll probably need that though
        if configuration["joins"]:
            # We can ignore left joins because they don't change the count
            join_sections = filter(lambda join: join["type"] != "LEFT", configuration["joins"])
            joins = " " + " ".join([join["raw"] for join in configuration["joins"]])
        else:
            joins = ""
        table_name = self._finalize_table_name(configuration["table_name"])
        if not configuration["group_by_column"]:
            query = f"SELECT COUNT(*) AS count FROM {table_name}{joins}{wheres}"
        else:
            group_by = self.group_by_clause(configuration["group_by_column"])
            query = (
                f"SELECT COUNT(*) AS count FROM (SELECT 1 FROM {table_name}{joins}{wheres}{group_by}) AS count_inner"
            )
        return [query, parameters]

    def _conditions_as_wheres_and_parameters(self, conditions, default_table_name):
        if not conditions:
            return ["", []]

        parameters = []
        where_parts = []
        for condition in conditions:
            parameters.extend(condition["values"])
            table = condition.get("table", default_table_name)
            if not table:
                table = default_table_name
            column = condition["column"]
            column_with_table = f"{table}.{column}"
            where_parts.append(
                self.condition_parser._with_placeholders(
                    column_with_table,
                    condition["operator"],
                    condition["values"],
                    escape=False,
                )
            )
        return [" WHERE " + " AND ".join(where_parts), parameters]

    def _check_query_configuration(self, configuration):
        for key in configuration.keys():
            if key not in self._allowed_configs:
                raise KeyError(f"CursorBackend does not support config '{key}'. You may be using the wrong backend")

        for key in self._required_configs:
            if key not in configuration:
                raise KeyError(f"Missing required configuration key {key}")

        if "pagination" not in configuration:
            configuration["pagination"] = {"start": 0}
        for key in self._allowed_configs:
            if not key in configuration:
                configuration[key] = [] if key[-1] == "s" else ""
        return configuration

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
