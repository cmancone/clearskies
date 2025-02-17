from functools import cmp_to_key
import inspect
from typing import Any, Callable, Type

from clearskies.autodoc.schema import Integer as AutoDocInteger
from clearskies.autodoc.schema import Schema as AutoDocSchema
import clearskies.model
import clearskies.query
from clearskies.backends.backend import Backend


class Null:
    def __lt__(self, other):
        return True

    def __gt__(self, other):
        return False

    def __eq__(self, other):
        return isinstance(other, Null) or other is None


# for some comparisons we prefer comparing floats, but we need to be able to
# fall back on string comparison
def gentle_float_conversion(value):
    try:
        return float(value)
    except:
        return value


def _sort(row_a: Any, row_b: Any, sorts: list[clearskies.query.Sort]) -> int:
    for sort in sorts:
        reverse = 1 if sort.direction.lower() == "asc" else -1
        value_a = row_a[sort.column_name] if sort.column_name in row_a else None
        value_b = row_b[sort.column_name] if sort.column_name in row_b else None
        if value_a == value_b:
            continue
        if value_a is None:
            return -1 * reverse
        if value_b is None:
            return 1 * reverse
        return reverse * (1 if value_a > value_b else -1)
    return 0


class MemoryTable:
    _table_name: str = ""
    _column_names: list[str] = []
    _rows: list[dict[str, Any]] = []
    null: Null = Null()
    _id_index: dict[int | str, int] = {}
    id_column_name: str = ""
    _next_id: int = 1
    _model_class: type[clearskies.model.Model] = None # type:  ignore

    # here be dragons.  This is not a 100% drop-in replacement for the equivalent SQL operators
    # https://codereview.stackexchange.com/questions/259198/in-memory-table-filtering-in-python
    _operator_lambda_builders = {
        "<=>": lambda column, values, null: lambda row: row.get(column, null) == values[0],
        "!=": lambda column, values, null: lambda row: row.get(column, null) != values[0],
        "<=": lambda column, values, null: lambda row: gentle_float_conversion(row.get(column, null))
        <= gentle_float_conversion(values[0]),
        ">=": lambda column, values, null: lambda row: gentle_float_conversion(row.get(column, null))
        >= gentle_float_conversion(values[0]),
        ">": lambda column, values, null: lambda row: gentle_float_conversion(row.get(column, null))
        > gentle_float_conversion(values[0]),
        "<": lambda column, values, null: lambda row: gentle_float_conversion(row.get(column, null))
        < gentle_float_conversion(values[0]),
        "=": lambda column, values, null: lambda row: (str(row[column]) if column in row else null) == str(values[0]),
        "is not null": lambda column, values, null: lambda row: (column in row and row[column] is not None),
        "is null": lambda column, values, null: lambda row: (column not in row or row[column] is None),
        "is not": lambda column, values, null: lambda row: row.get(column, null) != values[0],
        "is": lambda column, values, null: lambda row: row.get(column, null) == str(values[0]),
        "like": lambda column, values, null: lambda row: row.get(column, null) == str(values[0]),
        "in": lambda column, values, null: lambda row: row.get(column, null) in values,
    }

    def __init__(self, model_class: Type[clearskies.model.Model]) -> None:
        self._rows = []
        self._id_index = {}
        self.id_column_name = model_class.id_column_name
        self._next_id = 1
        self._model_class = model_class

        self._table_name = model_class.destination_name()
        self._column_names = list(model_class.get_columns().keys())
        if self.id_column_name not in self._column_names:
            self._column_names.append(self.id_column_name)

    def update(self, id: int | str, data: dict[str, Any]) -> dict[str, Any]:
        if id not in self._id_index:
            raise ValueError(f"Attempt to update non-existent record with '{self.id_column_name}' of '{id}'")
        index = self._id_index[id]
        row = self._rows[index]
        if row is None:
            raise ValueError(
                f"Cannot update record with '{self.id_column_name}' of '{id}' because it was already deleted"
            )
        for column_name in data.keys():
            if column_name not in self._column_names:
                raise ValueError(
                    f"Cannot update record: column '{column_name}' does not exist in table '{self._table_name}'"
                )
        self._rows[index] = {
            **self._rows[index],
            **data,
        }
        return self._rows[index]

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        for column_name in data.keys():
            if column_name not in self._column_names:
                raise ValueError(
                    f"Cannot create record: column '{column_name}' does not exist for model '{self._model_class.__name__}'"
                )
        incoming_id = data.get(self.id_column_name)
        if not incoming_id:
            incoming_id = self._next_id
            data[self.id_column_name] = incoming_id
            self._next_id += 1
        try:
            incoming_as_int = int(incoming_id)
            if incoming_as_int >= self._next_id:
                self._next_id = incoming_as_int + 1
        except:
            pass
        if incoming_id in self._id_index and self._rows[self._id_index[data[self.id_column_name]]] is not None:
            return self.update(data[self.id_column_name], data)
        for column_name in self._column_names:
            if column_name not in data:
                data[column_name] = None
        self._rows.append({**data})
        self._id_index[data[self.id_column_name]] = len(self._rows) - 1
        return data

    def delete(self, id):
        if id not in self._id_index:
            return True
        index = self._id_index[id]
        if self._rows[index] is None:
            return True
        # we set the row to None because if we remove it we'll change the indexes of the rest
        # of the rows, and I like being able to calculate the index from the id
        self._rows[index] = None
        return True

    def count(self, query: clearskies.query.Query):
        return len(self.rows(query, query.conditions, filter_only=True))

    def rows(self, query: clearskies.query.Query, conditions: list[clearskies.query.Condition], filter_only: bool=False, next_page_data: dict[str, Any] | None=None):
        rows = [*self._rows]
        for condition in conditions:
            rows = list(filter(self._condition_as_filter(condition), rows))
        rows = [*rows]
        if filter_only:
            return rows
        if query.sorts:
            rows = sorted(rows, key=cmp_to_key(lambda row_a, row_b: _sort(row_a, row_b, query.sorts)))
        if query.limit or query.pagination.get("start"):
            number_rows = len(rows)
            start = int(query.pagination.get("start", 0))
            if not start:
                start = 0
            if int(start) >= number_rows:
                start = number_rows - 1
            end = len(rows)
            if query.limit and start + int(query.limit) <= number_rows:
                end = start + int(query.limit)
            if end < number_rows and type(next_page_data) == dict:
                next_page_data["start"] = start + int(query.limit)
            rows = rows[start:end]
        return rows

    def _condition_as_filter(self, condition: clearskies.query.Condition) -> Callable:
        column = condition.column_name
        values = condition.values
        return self._operator_lambda_builders[condition.operator.lower()](column, values, self.null)


class MemoryBackend(Backend):
    _tables: dict[str, MemoryTable] = {}
    _silent_on_missing_tables: bool = False

    def __init__(self):
        self._tables = {}
        self._silent_on_missing_tables = True

    def silent_on_missing_tables(self, silent=True):
        self._silent_on_missing_tables = silent

    def create_table(self, model_class: Type[clearskies.model.Model]):
        table_name = model_class.destination_name()
        if table_name in self._tables:
            return
        self._tables[table_name] = MemoryTable(model_class)

    def has_table(self, model_class: Type[clearskies.model.Model]) -> bool:
        table_name = model_class.destination_name()
        return table_name in self._tables

    def get_table(self, model_class: Type[clearskies.model.Model], create_if_missing=False) -> MemoryTable:
        table_name = model_class.destination_name()
        if table_name not in self._tables:
            if create_if_missing:
                self.create_table(model_class)
            else:
                raise ValueError(f"The memory backend was asked to work with the model '{model_class.__name__}' but this model hasn't been explicitly added to the memory backend.  This typically means that you are querying for records in a model but haven't created any yet.")
        return self._tables[table_name]

    def update(self, id: int | str, data: dict[str, Any], model: clearskies.model.Model) -> dict[str, Any]:
        self.create_table(model.__class__)
        return self.get_table(model.__class__).update(id, data)

    def create(self, data: dict[str, Any], model: clearskies.model.Model) -> dict[str, Any]:
        self.create_table(model.__class__)
        return self.get_table(model.__class__).create(data)

    def delete(self, id: int | str, model: clearskies.model.Model) -> bool:
        self.create_table(model.__class__)
        return self.get_table(model.__class__).delete(id)

    def count(self, query: clearskies.query.Query) -> int:
        self.check_query(query)
        if not self.has_table(query.model_class):
            if self._silent_on_missing_tables:
                return 0

            raise ValueError(
                f"Attempt to count records for model '{query.model_class.__name__}' that hasn't yet been loaded into the MemoryBackend"
            )

        # this is easy if we have no joins, so just return early so I don't have to think about it
        if not query.joins:
            return self.get_table(query.model_class).count(query)

        # we can ignore left joins when counting
        query.joins = [join for join in query.joins if join.join_type != "LEFT"]
        return len(self.rows_with_joins(query))

    def records(self, query: clearskies.query.Query, next_page_data=None) -> list[dict[str, Any]]:
        self.check_query(query)
        if not self.has_table(query.model_class):
            if self._silent_on_missing_tables:
                return []

            raise ValueError(
                f"Attempt to fetch records for model '{query.model_class.__name__} that hasn't yet been loaded into the MemoryBackend"
            )

        # this is easy if we have no joins, so just return early so I don't have to think about it
        if not query.joins:
            return self.get_table(query.model_class).rows(query, query.conditions, next_page_data=next_page_data)

        rows = self.rows_with_joins(query)

        # currently we don't do much with selects, so just limit results down to the data from the original
        # table.
        rows = [row[query.model_class.destination_name()] for row in rows]

        if query.sorts:
            rows = sorted(rows, key=cmp_to_key(lambda row_a, row_b: _sort(row_a, row_b, query.sorts)))
        if "start" in query.pagination or query.limit:
            number_rows = len(rows)
            start = query.pagination.get("start", 0)
            if start >= number_rows:
                start = number_rows - 1
            end = len(rows)
            if query.limit and start + query.limit <= number_rows:
                end = start + query.limit
            rows = rows[start:end]
            if end < number_rows and type(next_page_data) == dict:
                next_page_data["start"] = start + query.limit
        return rows

    def rows_with_joins(self, query: clearskies.query.Query) -> list[dict[str, Any]]:
        joins = [*query.joins]
        conditions = [*query.conditions]
        # quick sanity check
        for join in query.joins:
            if join.unaliased_table_name not in self._tables:
                raise ValueError(
                    f"Join '{join._raw_join}' refrences table '{join.unaliased_table_name}' which does not exist in MemoryBackend"
                )

        # start with the matches in the main table
        left_table_name = query.model_class.destination_name()
        main_rows = self.get_table(query.model_class).rows(
            query, self.conditions_for_table(left_table_name, conditions, is_left=True), filter_only=True
        )
        # and now adjust the way data is stored in our rows list to support the joining process.
        # we're going to go from something like: `[{row_1}, {row_2}]` to something like:
        # [{table_1: table_1_row_1, table_2: table_2_row_1}, {table_1: table_1_row_2, table_2: table_2_row_2}]
        # etc...
        rows = [{left_table_name: row} for row in main_rows]
        joined_tables = [left_table_name]

        # and now work through our joins.  The tricky part is order - we need to manage the joins in the
        # proper order, but they may not be in the correcet order in our join list.  I still don't feel like building
        # a full graph, so cheat and be dumb: loop through them all and join in the ones we can, skipping the ones
        # we can't.  If we get to the end and there are still joins left in the queue, then repeat, and eventually
        # complain (since the joins may not be a valid object graph)
        for i in range(10):
            for index, join in enumerate(joins):
                left_table_name = join.left_table_name
                alias = join.alias
                right_table_name = join.right_table_name
                table_name_for_join = alias if alias else right_table_name
                if left_table_name not in joined_tables:
                    continue

                join_rows = self._tables[right_table_name].rows(
                    query, self.conditions_for_table(table_name_for_join, conditions, joined_tables), filter_only=True
                )

                rows = self.join_rows(rows, join_rows, join, joined_tables)

                # done with this one!
                del joins[index]
                joined_tables.append(table_name_for_join)

            # are we done yet?
            if not joins:
                break

        if joins:
            raise ValueError(
                "Unable to fulfill joins for query - perhaps a necessary join is missing? "
                + "One way to get this error is if you tried to join on another table which hasn't been "
                + "joined itself.  e.g.: SELECT * FROM users JOIN type ON type.id=categories.type_id"
            )

        return rows

    def all_rows(self, table_name: str) -> list[dict[str, Any]]:
        if table_name not in self._tables:
            if self._silent_on_missing_tables:
                return []

            raise ValueError(f"Cannot return rows for unknown table '{table_name}'")
        return self._tables[table_name]._rows

    def check_query(self, query: clearskies.query.Query) -> None:
        if query.group_by:
            raise KeyError(f"MemoryBackend does not support config group_by clauses in queries. You may be using the wrong backend.")

    def conditions_for_table(self, table_name: str, conditions: list[clearskies.query.Condition], is_left=False) -> list[clearskies.query.Condition]:
        """
        Returns only the conditions for the given table

        If you set is_left=True then it assumes this is the "default" table and so will also return conditions
        without a table name.
        """
        return [condition for condition in conditions if condition.table_name == table_name or (is_left and not condition.table_name)]

    def join_rows(self, rows: list[dict[str, Any]], join_rows: list[dict[str, Any]], join: clearskies.query.Join, joined_tables: list[str]) -> list[dict[str, Any]]:
        """
        Adds the rows in `join_rows` in to the `rows` holder.

        `rows` should be something like:

        ```
        [
            {
                'table_1': {'table_1_row_1'},
                'table_2': {'table_2_row_1'},
            },
            {
                'table_1': {'table_1_row_2'},
                'table_2': {'table_2_row_2'},
            }
        ]
        ```

        and join_rows should be the rows for the new table, something like:

        `[{table_3_row_1}, {table_3_row_2}]`

        which will then get merged into the rows variable properly (which it will return as a new list)
        """
        join_table_name = join.alias if join.alias else join.right_table_name
        join_type = join.join_type

        # loop through each entry in rows, find a matching table in join_rows, and take action depending on join type
        rows = [*rows]
        matched_right_row_indexes = []
        left_table_name = join.left_table_name
        left_column_name = join.left_column_name
        for row_index, row in enumerate(rows):
            matching_row = None
            if left_table_name not in row:
                raise ValueError("Attempted to check join data from unjoined table, which should not happen...")
            left_value = (
                row[left_table_name][left_column_name]
                if (row[left_table_name] is not None and left_column_name in row[left_table_name])
                else None
            )
            for join_index, join_row in enumerate(join_rows):
                right_value = join_row[join.right_column_name] if join.right_column_name in join_row else None
                # for now we are assuming the operator for the matching is `=`.  This is mainly because
                # our join parsing doesn't bother checking for the matching operator, because it is `=` in
                # 99% of cases.  We can always adjust down the line.
                if (right_value is None and left_value is None) or (right_value == left_value):
                    matching_row = join_row
                    matched_right_row_indexes.append(right_value)
                    break

            # next action depends on the join type and match success
            # for left and outer joins we always preserve records in the main table, so just plop in our match
            # (even if it is None)
            if join_type == "LEFT" or join_type == "OUTER":
                rows[row_index][join_table_name] = matching_row

            # for inner and right joins we delete the row if we don't have a match
            elif join_type == "INNER" or join_type == "RIGHT":
                if matching_row is not None:
                    rows[row_index][join_table_name] = matching_row
                else:
                    # we can't immediately delete the row because we're looping over the array it is in,
                    # so just mark it as None and remove it later
                    rows[row_index] = None # type: ignore

        rows = [row for row in rows if row is not None]

        # now for outer/right rows we add on any unmatched rows
        if (join_type == "OUTER" or join_type == "RIGHT") and len(matched_right_row_indexes) < len(join_rows):
            for join_index in set(range(len(join_rows))) - set(matched_right_row_indexes):
                rows.append(
                    {
                        join_table_name: join_rows[join_index],
                        **{table_name: None for table_name in joined_tables},
                    }
                )

        return rows

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

    def documentation_pagination_parameters(self, case_mapping: Callable[[str], str]) -> list[tuple[AutoDocSchema, str]]:
        return [
            (
                AutoDocInteger(case_mapping("start"), example=0),
                "The zero-indexed record number to start listing results from",
            )
        ]
