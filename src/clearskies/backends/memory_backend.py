from .backend import Backend
from collections import OrderedDict
from functools import cmp_to_key
import inspect


class Null:
    def __lt__(self, other):
        return True

    def __gt__(self, other):
        return False

    def __eq__(self, other):
        return isinstance(other, Null) or other is None

class MemoryTable:
    _table_name = None
    _column_names = None
    _rows = None
    null = None

    # here be dragons.  This is not a 100% drop-in replacement for the equivalent SQL operators
    # https://codereview.stackexchange.com/questions/259198/in-memory-table-filtering-in-python
    _operator_lambda_builders = {
        '<=>': lambda column, values, null: lambda row: row.get(column, null) == values[0],
        '!=': lambda column, values, null: lambda row: row.get(column, null) != values[0],
        '<=': lambda column, values, null: lambda row: row.get(column, null) <= values[0],
        '>=': lambda column, values, null: lambda row: row.get(column, null) >= values[0],
        '>': lambda column, values, null: lambda row: row.get(column, null) > values[0],
        '<': lambda column, values, null: lambda row: row.get(column, null) < values[0],
        '=': lambda column, values, null: lambda row: (str(row[column]) if column in row else null) == str(values[0]),
        'is not null': lambda column, values, null: lambda row: (column in row and row[column] is not None),
        'is null': lambda column, values, null: lambda row: (column not in row or row[column] is None),
        'is not': lambda column, values, null: lambda row: row.get(column, null) != values[0],
        'is': lambda column, values, null: lambda row: row.get(column, null) == str(values[0]),
        'like': lambda column, values, null: lambda row: row.get(column, null) == str(values[0]),
        'in': lambda column, values, null: lambda row: row.get(column, null) in values,
    }

    def __init__(self, model=None):
        self.null = Null()
        self._column_names = []
        self._rows = []

        if model is not None:
            self._table_name = model.table_name
            self._column_names.extend(model.columns_configuration().keys())

    def update(self, id, data):
        if id > len(self._rows) or id < 1:
            raise ValueError(f"Cannot update non existent record with id of '{id}'")
        index = id-1
        row = self._rows[index]
        if row is None:
            raise ValueError(f"Cannot update record with id of '{id}' because it was already deleted")
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
        if 'id' not in data:
            new_id = len(self._rows) + 1
            data['id'] = new_id
        for column_name in self._column_names:
            if column_name not in data:
                data[column_name] = None
        self._rows.append({**data})
        return data

    def delete(self, id):
        if id > len(self._rows) or id < 1:
            raise ValueError(f"Cannot delete non existent record with id of '{id}'")
        index = id-1
        if self._rows[index] is None:
            return True
        # we set the row to None because if we remove it we'll change the indexes of the rest
        # of the rows, and I like being able to calculate the index from the id
        self._rows[index] = None
        return True

    def count(self, configuration):
        return len(self.rows(configuration, filter_only=True))

    def rows(self, configuration, filter_only=False):
        rows = list(filter(None, self._rows))
        if 'wheres' in configuration and configuration['wheres']:
            for where in configuration['wheres']:
                rows = filter(self._where_as_filter(where), rows)
            rows = list(rows)
        if filter_only:
            return rows
        if 'sorts' in configuration and configuration['sorts']:
            rows = sorted(rows, key=cmp_to_key(lambda row_a, row_b: self._sort(row_a, row_b, configuration['sorts'])))
        if 'limit_start' in configuration or 'limit_length' in configuration:
            number_rows = len(rows)
            start = configuration['limit_start'] if 'limit_start' in configuration and configuration['limit_start'] else 0
            if start >= number_rows:
                start = number_rows-1
            end = len(rows)
            if 'limit_length' in configuration and configuration['limit_length'] and start + configuration['limit_length'] <= number_rows:
                end = start + configuration['limit_length']
            rows = rows[start:end]
        return rows

    def _where_as_filter(self, where):
        column = where['column']
        values = where['values']
        return self._operator_lambda_builders[where['operator']](column, values, self.null)

    def _sort(self, row_a, row_b, sorts):
        for sort in sorts:
            reverse = 1 if sort['direction'].lower() == 'asc' else -1
            value_a = row_a[sort['column']] if sort['column'] in row_a else None
            value_b = row_b[sort['column']] if sort['column'] in row_b else None
            if value_a == value_b:
                continue
            if value_a is None:
                return -1*reverse
            if value_b is None:
                return 1*reverse
            return reverse*(1 if value_a > value_b else -1)
        return 0

class MemoryBackend(Backend):
    _tables = None
    _silent_on_missing_tables = False

    _allowed_configs = [
        'table_name',
        'wheres',
        'sorts',
        'limit_start',
        'limit_length',
        'selects',
    ]

    _required_configs = [
        'table_name',
    ]

    def __init__(self):
        self._tables = {}
        self._silent_on_missing_tables = False

    def silent_on_missing_tables(self, silent=False):
        self._silent_on_missing_tables = silent

    def configure(self):
        pass

    def create_table(self, model):
        """
        Accepts either a model or a model class and creates a "table" for it
        """
        model = self.cheez_model(model)
        if model.table_name in self._tables:
            return
        self._tables[model.table_name] = MemoryTable(model=model)

    def update(self, id, data, model):
        self.create_table(model)
        return self._tables[model.table_name].update(id, data)

    def create(self, data, model):
        self.create_table(model)
        return self._tables[model.table_name].create(data)

    def delete(self, id, model):
        self.create_table(model)
        return self._tables[model.table_name].delete(id)

    def count(self, configuration):
        if configuration['table_name'] not in self._tables:
            if self._silent_on_missing_tables:
                return 0

            raise ValueError(
                f"Attempt to count records in non-existent table '{configuration['table_name']} via MemoryBackend"
            )
        return self._tables[configuration['table_name']].count(configuration)

    def records(self, configuration):
        table_name = configuration['table_name']
        if table_name not in self._tables:
            if self._silent_on_missing_tables:
                return []

            raise ValueError(
                f"Attempt to fetch records from non-existent table '{configuration['table_name']} via MemoryBackend"
            )
        return self._tables[table_name].rows(configuration)

    def all_rows(self, table_name):
        if table_name not in self._tables:
            if self._silent_on_missing_tables:
                return []

            raise ValueError(f"Cannot return rows for unknown table '{table_name}'")
        return self._tables[table_name]._rows

    def _check_query_configuration(self, configuration):
        for key in configuration.keys():
            if key not in self._allowed_configs:
                raise KeyError(
                    f"MemoryBackend does not support config '{key}'. You may be using the wrong backend"
                )
        for key in self._required_configs:
            if key not in configuration:
                raise KeyError(f'Missing required configuration key {key}')

        for key in self._allowed_configs:
            if not key in configuration:
                configuration[key] = [] if key[-1] == 's' else ''
        return configuration
