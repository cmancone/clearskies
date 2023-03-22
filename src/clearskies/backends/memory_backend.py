from .backend import Backend
from collections import OrderedDict
from functools import cmp_to_key
import inspect
from typing import Any, Callable, Dict, List, Tuple
from ..autodoc.schema import Integer as AutoDocInteger
from .. import model
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
def _sort(row_a, row_b, sorts):
    for sort in sorts:
        reverse = 1 if sort['direction'].lower() == 'asc' else -1
        value_a = row_a[sort['column']] if sort['column'] in row_a else None
        value_b = row_b[sort['column']] if sort['column'] in row_b else None
        if value_a == value_b:
            continue
        if value_a is None:
            return -1 * reverse
        if value_b is None:
            return 1 * reverse
        return reverse * (1 if value_a > value_b else -1)
    return 0
class MemoryTable:
    _table_name = None
    _column_names = None
    _rows = None
    null = None
    _id_index = None
    id_column_name = None
    _next_id = None

    # here be dragons.  This is not a 100% drop-in replacement for the equivalent SQL operators
    # https://codereview.stackexchange.com/questions/259198/in-memory-table-filtering-in-python
    _operator_lambda_builders = {
        '<=>':
        lambda column, values, null: lambda row: row.get(column, null) == values[0],
        '!=':
        lambda column, values, null: lambda row: row.get(column, null) != values[0],
        '<=':
        lambda column, values, null: lambda row: gentle_float_conversion(row.get(column, null)
                                                                         ) <= gentle_float_conversion(values[0]),
        '>=':
        lambda column, values, null: lambda row: gentle_float_conversion(row.get(column, null)
                                                                         ) >= gentle_float_conversion(values[0]),
        '>':
        lambda column, values, null: lambda row: gentle_float_conversion(row.get(column, null)
                                                                         ) > gentle_float_conversion(values[0]),
        '<':
        lambda column, values, null: lambda row: gentle_float_conversion(row.get(column, null)) <
        gentle_float_conversion(values[0]),
        '=':
        lambda column, values, null: lambda row: (str(row[column]) if column in row else null) == str(values[0]),
        'is not null':
        lambda column, values, null: lambda row: (column in row and row[column] is not None),
        'is null':
        lambda column, values, null: lambda row: (column not in row or row[column] is None),
        'is not':
        lambda column, values, null: lambda row: row.get(column, null) != values[0],
        'is':
        lambda column, values, null: lambda row: row.get(column, null) == str(values[0]),
        'like':
        lambda column, values, null: lambda row: row.get(column, null) == str(values[0]),
        'in':
        lambda column, values, null: lambda row: row.get(column, null) in values,
    }

    def __init__(self, model):
        self.null = Null()
        self._column_names = []
        self._rows = []
        self._id_index = {}
        self.id_column_name = model.id_column_name
        self._next_id = 1

        self._table_name = model.table_name()
        self._column_names.extend(model.columns_configuration().keys())
        if self.id_column_name not in self._column_names:
            self._column_names.append(self.id_column_name)

    def update(self, id, data):
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

    def create(self, data):
        for column_name in data.keys():
            if column_name not in self._column_names:
                raise ValueError(
                    f"Cannot create record: column '{column_name}' does not exist in table '{self._table_name}'"
                )
        incoming_id = data.get(self.id_column_name)
        if not incoming_id:
            incoming_id = self._next_id
            data[self.id_column_name] = incoming_id
            self._next_id += 1
        try:
            incoming_as_int = int(incoming_as_int)
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

    def count(self, configuration, wheres):
        return len(self.rows(configuration, wheres, filter_only=True))

    def rows(self, configuration, wheres, filter_only=False, next_page_data=None):
        rows = list(filter(None, self._rows))
        for where in wheres:
            rows = filter(self._where_as_filter(where), rows)
        rows = list(rows)
        if filter_only:
            return rows
        if 'sorts' in configuration and configuration['sorts']:
            rows = sorted(rows, key=cmp_to_key(lambda row_a, row_b: _sort(row_a, row_b, configuration['sorts'])))
        if 'limit' in configuration or ('pagination' in configuration and configuration['pagination'].get('start')):
            number_rows = len(rows)
            start = int(configuration.get('pagination', {}).get('start', 0))
            if not start:
                start = 0
            if int(start) >= number_rows:
                start = number_rows - 1
            end = len(rows)
            if configuration.get('limit') and start + int(configuration['limit']) <= number_rows:
                end = start + int(configuration['limit'])
            if end < number_rows and type(next_page_data) == dict:
                next_page_data['start'] = start + configuration['limit']
            rows = rows[start:end]
        return rows

    def _where_as_filter(self, where):
        column = where['column']
        values = where['values']
        return self._operator_lambda_builders[where['operator'].lower()](column, values, self.null)
class MemoryBackend(Backend):
    _tables = None
    _silent_on_missing_tables = False

    _allowed_configs = [
        'table_name',
        'wheres',
        'joins',
        'sorts',
        'pagination',
        'length',
        'selects',
        'select_all',
        'model_columns',
    ]

    _required_configs = [
        'table_name',
    ]

    def __init__(self):
        self._tables = {}
        self._silent_on_missing_tables = True

    def silent_on_missing_tables(self, silent=True):
        self._silent_on_missing_tables = silent

    def configure(self):
        pass

    def create_table(self, model):
        """
        Accepts either a model or a model class and creates a "table" for it
        """
        model = self.cheez_model(model)
        if model.table_name() in self._tables:
            return
        self._tables[model.table_name()] = MemoryTable(model)

    def update(self, id, data, model):
        self.create_table(model)
        return self._tables[model.table_name()].update(id, data)

    def create(self, data, model):
        self.create_table(model)
        return self._tables[model.table_name()].create(data)

    def delete(self, id, model):
        self.create_table(model)
        return self._tables[model.table_name()].delete(id)

    def count(self, configuration, model):
        if configuration['table_name'] not in self._tables:
            if self._silent_on_missing_tables:
                return 0

            raise ValueError(
                f"Attempt to count records in non-existent table '{configuration['table_name']} via MemoryBackend"
            )

        # this is easy if we have no joins, so just return early so I don't have to think about it
        if 'joins' not in configuration or not configuration['joins']:
            wheres = configuration['wheres'] if 'wheres' in configuration else []
            return self._tables[configuration['table_name']].count(configuration, wheres)

        # we can ignore left joins when counting
        configuration = {**configuration}
        configuration['joins'] = [join for join in configuration['joins'] if join['type'] != 'LEFT']
        return len(self.rows_with_joins(configuration))

    def records(self, configuration, model, next_page_data=None):
        table_name = configuration['table_name']
        if table_name not in self._tables:
            if self._silent_on_missing_tables:
                return []

            raise ValueError(
                f"Attempt to fetch records from non-existent table '{configuration['table_name']} via MemoryBackend"
            )

        # this is easy if we have no joins, so just return early so I don't have to think about it
        if 'joins' not in configuration or not configuration['joins']:
            wheres = configuration['wheres'] if 'wheres' in configuration else []
            return self._tables[table_name].rows(configuration, wheres, next_page_data=next_page_data)

        rows = self.rows_with_joins(configuration)

        # currently we don't do much with selects, so just limit results down to the data from the original
        # table.
        rows = [row[table_name] for row in rows]

        if 'sorts' in configuration and configuration['sorts']:
            rows = sorted(rows, key=cmp_to_key(lambda row_a, row_b: _sort(row_a, row_b, configuration['sorts'])))
        if 'start' in configuration.get('pagination', {}) or 'limit' in configuration:
            number_rows = len(rows)
            start = configuration.get('pagination', {}).get('start', 0)
            if start >= number_rows:
                start = number_rows - 1
            end = len(rows)
            if configuration.get('limit') and start + configuration.get('limit') <= number_rows:
                end = start + configuration.get('limit')
            rows = rows[start:end]
            if end < number_rows and type(next_page_data) == dict:
                next_page_data['start'] = start + configuration['limit']
        return rows

    def rows_with_joins(self, configuration):
        joins = configuration['joins']
        wheres = configuration['wheres'] if 'wheres' in configuration else []
        # quick sanity check
        for join in configuration['joins']:
            if join['table'] not in self._tables:
                raise ValueError(
                    f"Join '{join['raw']}' refrences table '{join['table']}' which does not exist in MemoryBackend"
                )

        # start with the matches in the main table
        left_table = configuration['table_name']
        main_rows = self._tables[left_table].rows(
            configuration, self._wheres_for_table(left_table, wheres, is_left=True), filter_only=True
        )
        # and now adjust the way data is stored in our rows list to support the joining process.
        # we're going to go from something like: `[{row_1}, {row_2}]` to something like:
        # [{table_1: table_1_row_1, table_2: table_2_row_1}, {table_1: table_1_row_2, table_2: table_2_row_2}]
        # etc...
        rows = [{left_table: row} for row in main_rows]
        joined_tables = [left_table]

        # and now work through our joins.  The tricky part is order - we need to manage the joins in the
        # proper order, but they may not be in the correcet order in our join list.  I still don't feel like building
        # a full graph, so cheat and be dumb: loop through them all and join in the ones we can, skipping the ones
        # we can't.  If we get to the end and there are still joins left in the queue, then repeat, and eventually
        # complain (since the joins may not be a valid object graph)
        for i in range(10):
            for (index, join) in enumerate(joins):
                left_table = join['left_table']
                alias = join['alias']
                right_table = join['right_table']
                table_name_for_join = alias if alias else right_table
                if left_table not in joined_tables:
                    continue

                join_rows = self._tables[right_table].rows(
                    configuration, self._wheres_for_table(table_name_for_join, wheres, joined_tables), filter_only=True
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
                "Unable to fulfill joins for query - perhaps a necessary join is missing? " + \
                "One way to get this error is if you tried to join on another table which hasn't been " + \
                "joined itself.  e.g.: SELECT * FROM users JOIN type ON type.id=categories.type_id"
            )

        return rows

    def all_rows(self, table_name):
        if table_name not in self._tables:
            if self._silent_on_missing_tables:
                return []

            raise ValueError(f"Cannot return rows for unknown table '{table_name}'")
        return self._tables[table_name]._rows

    def _check_query_configuration(self, configuration):
        for key in configuration.keys():
            if key not in self._allowed_configs:
                raise KeyError(f"MemoryBackend does not support config '{key}'. You may be using the wrong backend")
        for key in self._required_configs:
            if key not in configuration:
                raise KeyError(f'Missing required configuration key {key}')

        for key in self._allowed_configs:
            if not key in configuration:
                configuration[key] = [] if key[-1] == 's' else ''
        if 'pagination' not in configuration or 'start' not in configuration['pagination']:
            configuration['pagination'] = {'start': 0}
        return configuration

    def _wheres_for_table(self, table_name, wheres, is_left=False):
        """
        Returns only the where conditions for the current table

        If you set is_left=True then it assumes this is the "default" table and so will also return conditions
        without a table name.
        """
        return [where for where in wheres if where['table'] == table_name or (is_left and not where['table'])]

    def join_rows(self, rows, join_rows, join_config, joined_tables):
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
        join_table_name = join_config['alias'] if join_config['alias'] else join_config['right_table']
        join_type = join_config['type']

        # loop through each entry in rows, find a matching table in join_rows, and take action depending on join type
        rows = [*rows]
        matched_right_row_indexes = []
        left_table = join_config['left_table']
        left_column = join_config['left_column']
        for (row_index, row) in enumerate(rows):
            matching_row = None
            if left_table not in row:
                raise ValueError("Attempted to check join data from unjoined table, which should not happen...")
            left_value = row[left_table][left_column] if (
                row[left_table] is not None and left_column in row[left_table]
            ) else None
            for (join_index, join) in enumerate(join_rows):
                right_value = join[join_config['right_column']] if join_config['right_column'] in join else None
                # for now we are assuming the operator for the matching is `=`.  This is mainly because
                # our join parsing doesn't bother checking for the matching operator, because it is `=` in
                # 99% of cases.  We can always adjust down the line.
                if (right_value is None and left_value is None) or (right_value == left_value):
                    matching_row = join
                    matched_right_row_indexes.append(right_value)
                    break

            # next action depends on the join type and match success
            # for left and outer joins we always preserve records in the main table, so just plop in our match
            # (even if it is None)
            if join_type == 'LEFT' or join_type == 'OUTER':
                rows[row_index][join_table_name] = matching_row

            # for inner and right joins we delete the row if we don't have a match
            elif join_type == 'INNER' or join_type == 'RIGHT':
                if matching_row is not None:
                    rows[row_index][join_table_name] = matching_row
                else:
                    # we can't immediately delete the row because we're looping over the array it is in,
                    # so just mark it as None and remove it later
                    rows[row_index] = None

        rows = [row for row in rows if row is not None]

        # now for outer/right rows we add on any unmatched rows
        if (join_type == 'OUTER' or join_type == 'RIGHT') and len(matched_right_row_indexes) < len(join_rows):
            for join_index in set(enumerate(join_rows)) - set(matched_right_row_indexes):
                rows.append({
                    join_table_name: join_rows[join_index],
                    **{table_name: None
                       for table_name in joined_tables},
                })

        return rows

    def validate_pagination_kwargs(self, kwargs: Dict[str, Any], case_mapping: Callable) -> str:
        extra_keys = set(kwargs.keys()) - set(self.allowed_pagination_keys())
        if len(extra_keys):
            key_name = case_mapping('start')
            return "Invalid pagination key(s): '" + "','".join(extra_keys) + f"'.  Only '{key_name}' is allowed"
        if 'start' not in kwargs:
            key_name = case_mapping('start')
            return f"You must specify '{key_name}' when setting pagination"
        start = kwargs['start']
        try:
            start = int(start)
        except:
            key_name = case_mapping('start')
            return f"Invalid pagination data: '{key_name}' must be a number"
        return ''

    def allowed_pagination_keys(self) -> List[str]:
        return ['start']

    def documentation_pagination_next_page_response(self, case_mapping: Callable) -> List[Any]:
        return [AutoDocInteger(case_mapping('start'), example=10)]

    def documentation_pagination_next_page_example(self, case_mapping: Callable) -> Dict[str, Any]:
        return {case_mapping('start'): 10}

    def documentation_pagination_parameters(self, case_mapping: Callable) -> List[Tuple[Any]]:
        return [(
            AutoDocInteger(case_mapping('start'),
                           example=10), 'The zero-indexed record number to start listing results from'
        )]
