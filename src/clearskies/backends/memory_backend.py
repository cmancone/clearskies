from .backend import Backend
from collections import OrderedDict


class MemoryTable:
    _table_name = None
    _column_names = None
    _rows = None
    _id_to_index = None
    _next_id = 1

    # here be dragons.  This is not a 100% drop-in replacement for the equivalent SQL operators
    _operator_lambda_builders = {
        '<=>': lambda column, values: lambda row: (row[column] if column in row else None) == values[0],
        '!=': lambda column, values: lambda row: (row[column] if column in row else None) != values[0],
        '<=': lambda column, values: lambda row: (row[column] if column in row else None) <= values[0],
        '>=': lambda column, values: lambda row: (row[column] if column in row else None) >= values[0],
        '>': lambda column, values: lambda row: (row[column] if column in row else None) > values[0],
        '<': lambda column, values: lambda row: (row[column] if column in row else None) < values[0],
        '=': lambda column, values: lambda row: (row[column] if column in row else None) == values[0],
        'is not null': lambda column, values: lambda row: (column in row and row[column] is not None),
        'is null': lambda column, values: lambda row: (column not in row or row[column] is None),
        'is not': lambda column, values: lambda row: (row[column] if column in row else None) != values[0],
        'is': lambda column, values: lambda row: (row[column] if column in row else None) == values[0],
        'like': lambda column, values: lambda row: (row[column] if column in row else None) == values[0],
        'in': lambda column, values: lambda row: (row[column] if column in row else None) in values,
    }

    def __init__(self, model=None):
        self._column_names = []
        self._rows = []
        self._id_to_index = {}
        self._table_name = model.table_name

        if model is not None:
            self._column_names.extend(model.columns_configuration().keys())

    def add_index(self, column_name):
        if not column_name in self._indexes:
            self._indexes[column_name] = OrderedDict()
        if not column_name in self._column_names:
            self._column_names.append(column_name)

    def update(self, id, data):
        if id not in self._id_to_index:
            raise ValueError(f"Cannot update non existent record with id of '{id}'")
        index = self._id_to_index[id]
        if index is None:
            raise ValueError(f"Cannot update record with id of '{id}' because it was already deleted")
        for column_name in data.items():
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
        self._next_id += 1
        new_id = self._next_id
        data['id'] = new_id
        for column_name in self._column_names:
            if column_name not in data:
                data[column_name] = None
        self._rows.append(data)
        self._id_to_index[new_id] = len(self._rows)-1
        return self._rows

    def delete(self, id):
        if id not in self._id_to_index:
            return
        index = self._id_to_index[id]
        if row_index is None:
            return True
        row = self._rows[row_index]
        if row is None:
            return True
        # we set the row to None because if we remove it we'll change the indexes of the rest
        # of the rows, and break our `self._id_to_index` map
        self._rows[row_index] = None
        self._id_to_index[id] = None

    def count(self, configuration):
        return len(self.rows(configuration))

    def rows(self, configuration):
        if 'wheres' in configuration:
            rows = self._rows
            for where in configuration:
                rows = filter(self._where_as_filter(where), rows)
            rows = list(rows)
        else:
            rows = [*self._rows]

    def _where_as_filter(where):
        column = where['column']
        values = where['values']
        return self._operator_lambda_builders[where['operator']](column, values)


class MemoryBackend(Backend):
    _tables = None
    _iterator_index = -1
    _iterator_rows = []

    _allowed_configs = [
        'table_name',
        'wheres',
        'sorts',
        'group_by_column',
        'limit_start',
        'limit_length',
        'selects',
    ]

    _required_configs = [
        'table_name',
    ]

    def __init__(self):
        self._tables = {}
        self._iterator_index = -1
        self._iterator_rows = []

    def configure(self):
        pass

    def create_table(self, model):
        if model.table_name in self._tables:
            return
        self._tables[model.table_name] = Table(model)

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
            return 0
        return self._tables[configuration['table_name']].count(configuration)

    def iterator(self, configuration):
        table_name = configuration['table_name']
        self._iterator_rows = []
        self._iterator_index = -1
        if table_name in self._tables:
            self._iterator_rows = self._tables[table_name].rows(configuration)

    def next(self):
        self._iterator_index += 1
        if self._iterator_index >= len(self._iterator_rows):
            raise StopIteration()
        return self._iterator_rows[self._iterator_index]

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
