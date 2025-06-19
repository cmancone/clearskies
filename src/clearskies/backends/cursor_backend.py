from typing import Any, Callable

import clearskies.model
import clearskies.query
from clearskies.autodoc.schema import Integer as AutoDocInteger
from clearskies.autodoc.schema import Schema as AutoDocSchema
from clearskies.backends.backend import Backend
from clearskies.di import InjectableProperties, inject


class CursorBackend(Backend, InjectableProperties):
    """
    The cursor backend connects your models to a MySQL or MariaDB database.

    ## Installing Dependencies

    clearskies uses PyMySQL to manage the database connection and make queries.  This is not installed by default,
    but is a named extra that you can install when needed via:

    ```bash
    pip install clear-skies[mysql]
    ```

    ## Connecting to your server

    By default, database credentials are expected in environment variables:

    | Name        | Default | Value                                                         |
    |-------------|---------|---------------------------------------------------------------|
    | db_host     |         | The hostname where the database can be found                  |
    | db_username |         | The username to connect as                                    |
    | db_password |         | The password to connect with                                  |
    | db_database |         | The name of the database to use                               |
    | db_port     | 3306    | The network port to connect to                                |
    | db_ssl_ca   |         | Path to a certificate to use: enables SSL over the connection |

    However, you can fully control the credential provisioning process by declaring a dependency named `connection_details` and
    setting it to a dictionary with the above keys, minus the `db_` prefix:

    ```python
    class ConnectionDetails(clearskies.di.AdditionalConfig):
        provide_connection_details(self, secrets):
            return {
                "host": secrets.get("database_host"),
                "username": secrets.get("db_username"),
                "password": secrets.get("db_password"),
                "database": secrets.get("db_database"),
                "port": 3306,
                "ssl_ca": "/path/to/ca",
            }

    wsgi = clearskies.contexts.Wsgi(
        some_application,
        additional_configs=[ConnectionDetails()],
        bindings={
            "secrets": "" # some configuration here to point to your secret manager
        }
    )
    ```

    Similarly, some alternate credential provisioning schemes are built into clearskies.  See the
    clearskies.secrets.additional_configs module for those options.

    ## Connecting models to tables

    The table name for your model comes from calling the `destination_name` class method of the model class.  By
    default, this takes the class name, converts it to snake case, and then pluralizes it.  So, if you have a model
    class named `UserPreference` then the cursor backend will look for a table called `user_preferences`.  If this
    isn't what you want, then you can simply override `destination_name` to return whatever table you want:

    ```python
    class UserPreference(clearskies.Model):
        @classmethod
        def destination_name(cls):
            return "some_other_table_name"
    ```

    Additionally, the cursor backend accepts an argument called `table_prefix` which, if provided, will be prefixed
    to your table name.  Finally, you can declare a dependency called `global_table_prefix` which will automatically
    be added to every table name.  In the following example, the table name will be `user_configuration_preferences`
    due to:

     1. The `destination_name` method sets the table name to `preferences`
     2. The `table_prefix` argument to the CursorBackend constructor adds a prefix of `configuration_`
     3. The `global_table_prefix` binding sets a prefix of `user_`, wihch goes before everything else.

    ```python
    import clearskies


    class UserPreference(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.CursorBackend(table_prefix="configuration_")
        id = clearskies.columns.Uuid()

        @classmethod
        def destination_name(cls):
            return "preferences"


    cli = clearskies.contexts.Cli(
        clearskies.endpoints.Callable(
            lambda user_preferences: user_preferences.create(no_data=True).id,
        ),
        classes=[UserPreference],
        bindings={
            "global_table_prefix": "user_",
        },
    )
    ```

    """

    supports_n_plus_one = True
    cursor = inject.ByName("cursor")
    global_table_prefix = inject.ByName("global_table_prefix")
    table_escape_character = "`"
    column_escape_character = "`"
    table_prefix = ""

    def __init__(self, table_escape_character="`", column_escape_character="`", table_prefix=""):
        self.table_escape_character = table_escape_character
        self.column_escape_character = column_escape_character
        self.table_prefix = table_prefix

    def _finalize_table_name(self, table_name):
        table_name = f"{self.global_table_prefix}{self.table_prefix}{table_name}"
        if "." not in table_name:
            return f"{self.table_escape_character}{table_name}{self.table_escape_character}"
        return (
            self.table_escape_character
            + f"{self.table_escape_character}.{self.table_escape_character}".join(table_name.split("."))
            + self.table_escape_character
        )

    def update(self, id: int | str, data: dict[str, Any], model: clearskies.model.Model) -> dict[str, Any]:
        query_parts = []
        parameters = []
        escape = self.column_escape_character
        for key, val in data.items():
            query_parts.append(f"{escape}{key}{escape}=%s")
            parameters.append(val)
        updates = ", ".join(query_parts)

        # update the record
        table_name = self._finalize_table_name(model.destination_name())
        self.cursor.execute(
            f"UPDATE {table_name} SET {updates} WHERE {model.id_column_name}=%s", tuple([*parameters, id])
        )

        # and now query again to fetch the updated record.
        return self.records(
            clearskies.query.Query(
                model.__class__, conditions=[clearskies.query.Condition(f"{model.id_column_name}={id}")]
            )
        )[0]

    def create(self, data: dict[str, Any], model: clearskies.model.Model) -> dict[str, Any]:
        escape = self.column_escape_character
        columns = escape + f"{escape}, {escape}".join(data.keys()) + escape
        placeholders = ", ".join(["%s" for i in range(len(data))])

        table_name = self._finalize_table_name(model.destination_name())
        self.cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", tuple(data.values()))
        new_id = data.get(model.id_column_name)
        if not new_id:
            new_id = self.cursor.lastrowid
        if not new_id:
            raise ValueError("I can't figure out what the id is for a newly created record :(")

        return self.records(
            clearskies.query.Query(
                model.__class__, conditions=[clearskies.query.Condition(f"{model.id_column_name}={new_id}")]
            )
        )[0]

    def delete(self, id: int | str, model: clearskies.model.Model) -> bool:
        table_name = self._finalize_table_name(model.destination_name())
        self.cursor.execute(f"DELETE FROM {table_name} WHERE {model.id_column_name}=%s", (id,))
        return True

    def count(self, query: clearskies.query.Query) -> int:
        (sql, parameters) = self.as_count_sql(query)
        self.cursor.execute(sql, parameters)
        for row in self.cursor:
            return row[0] if type(row) == tuple else row["count"]
        return 0

    def records(
        self, query: clearskies.query.Query, next_page_data: dict[str, str | int] | None = None
    ) -> list[dict[str, Any]]:
        # I was going to get fancy and have this return an iterator, but since I'm going to load up
        # everything into a list anyway, I may as well just return the list, right?
        (sql, parameters) = self.as_sql(query)
        self.cursor.execute(sql, parameters)
        records = [row for row in self.cursor]
        if type(next_page_data) == dict:
            limit = query.limit
            start = query.pagination.get("start", 0)
            if limit and len(records) == limit:
                next_page_data["start"] = int(start) + int(limit)
        return records

    def as_sql(self, query: clearskies.query.Query) -> tuple[str, tuple[Any]]:
        escape = self.column_escape_character
        table_name = query.model_class.destination_name()
        (wheres, parameters) = self.conditions_as_wheres_and_parameters(
            query.conditions, query.model_class.destination_name()
        )
        select_parts = []
        if query.select_all:
            select_parts.append(self._finalize_table_name(table_name) + ".*")
        if query.selects:
            select_parts.extend(query.selects)
        select = ", ".join(select_parts)
        if query.joins:
            joins = " " + " ".join([join._raw_join for join in query.joins])
        else:
            joins = ""
        if query.sorts:
            sort_parts = []
            for sort in query.sorts:
                table_name = sort.table_name
                column_name = sort.column_name
                direction = sort.direction
                prefix = self._finalize_table_name(table_name) + "." if table_name else ""
                sort_parts.append(f"{prefix}{escape}{column_name}{escape} {direction}")
            order_by = " ORDER BY " + ", ".join(sort_parts)
        else:
            order_by = ""
        group_by = self.group_by_clause(query.group_by)
        limit = ""
        if query.limit:
            start = 0
            limit_size = int(query.limit)
            if "start" in query.pagination:
                start = int(query.pagination["start"])
            limit = f" LIMIT {start}, {limit_size}"

        table_name = self._finalize_table_name(table_name)
        return (
            f"SELECT {select} FROM {table_name}{joins}{wheres}{group_by}{order_by}{limit}".strip(),
            parameters,
        )

    def as_count_sql(self, query: clearskies.query.Query) -> tuple[str, tuple[Any]]:
        escape = self.column_escape_character
        # note that this won't work if we start including a HAVING clause
        (wheres, parameters) = self.conditions_as_wheres_and_parameters(
            query.conditions, query.model_class.destination_name()
        )
        # we also don't currently support parameters in the join clause - I'll probably need that though
        if query.joins:
            # We can ignore left joins because they don't change the count
            join_sections = filter(lambda join: join.type != "LEFT", query.joins)  # type: ignore
            joins = " " + " ".join([join._raw_join for join in join_sections])
        else:
            joins = ""
        table_name = self._finalize_table_name(query.model_class.destination_name())
        if not query.group_by:
            query_string = f"SELECT COUNT(*) AS count FROM {table_name}{joins}{wheres}"
        else:
            group_by = self.group_by_clause(query.group_by)
            query_string = (
                f"SELECT COUNT(*) AS count FROM (SELECT 1 FROM {table_name}{joins}{wheres}{group_by}) AS count_inner"
            )
        return (query_string, parameters)

    def conditions_as_wheres_and_parameters(
        self, conditions: list[clearskies.query.Condition], default_table_name: str
    ) -> tuple[str, tuple[Any]]:
        if not conditions:
            return ("", ())  # type: ignore

        parameters = []
        where_parts = []
        for condition in conditions:
            parameters.extend(condition.values)
            table = condition.table_name if condition.table_name else self._finalize_table_name(default_table_name)
            column = condition.column_name
            where_parts.append(
                condition._with_placeholders(
                    f"{table}.{column}",
                    condition.operator,
                    condition.values,
                    escape=False,
                )
            )
        return (" WHERE " + " AND ".join(where_parts), tuple(parameters))  # type: ignore

    def group_by_clause(self, group_by: str) -> str:
        if not group_by:
            return ""
        escape = self.column_escape_character
        if "." not in group_by:
            return f" GROUP BY {escape}{group_by}{escape}"
        parts = group_by.split(".", 1)
        table = parts[0]
        column = parts[1]
        return f" GROUP BY {escape}{table}{escape}.{escape}{column}{escape}"

    def validate_pagination_data(self, data: dict[str, Any], case_mapping: Callable) -> str:
        extra_keys = set(data.keys()) - set(self.allowed_pagination_keys())
        if len(extra_keys):
            key_name = case_mapping("start")
            return "Invalid pagination key(s): '" + "','".join(extra_keys) + f"'.  Only '{key_name}' is allowed"
        if "start" not in data:
            key_name = case_mapping("start")
            return f"You must specify '{key_name}' when setting pagination"
        start = data["start"]
        try:
            start = int(start)
        except:
            key_name = case_mapping("start")
            return f"Invalid pagination data: '{key_name}' must be a number"
        return ""

    def allowed_pagination_keys(self) -> list[str]:
        return ["start"]

    def documentation_pagination_next_page_response(self, case_mapping: Callable[[str], str]) -> list[Any]:
        return [AutoDocInteger(case_mapping("start"), example=0)]

    def documentation_pagination_next_page_example(self, case_mapping: Callable[[str], str]) -> dict[str, Any]:
        return {case_mapping("start"): 0}

    def documentation_pagination_parameters(
        self, case_mapping: Callable[[str], str]
    ) -> list[tuple[AutoDocSchema, str]]:
        return [
            (
                AutoDocInteger(case_mapping("start"), example=0),
                "The zero-indexed record number to start listing results from",
            )
        ]
