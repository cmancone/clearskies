from abc import ABC, abstractmethod
from .condition_parser import ConditionParser


class Models(ABC, ConditionParser):
    # The database connection
    _backend = None
    _columns = None
    _model_columns = None
    wheres = None
    sorts = None
    group_by_column = None
    limit_start = None
    limit_length = None
    selects = None
    must_rexecute = True
    must_recount = True
    count = None
    _table_name = None

    def __init__(self, backend, columns):
        self._backend = backend
        self._columns = columns
        self._model_columns = None
        self.wheres = []
        self.sorts = []
        self.group_by_column = None
        self.joins = []
        self.limit_start = 0
        self.limit_length = None
        self.selects = None
        self.must_rexecute = True
        self.must_recount = True

    @abstractmethod
    def model_class(self):
        """ Return the model class that this models object will find/return instances of """
        pass

    def clone(self):
        clone = self.blank()
        clone.configuration = self.configuration
        return clone

    def blank(self):
        return self.__class__(self._backend, self._columns)

    def get_table_name(self):
        if self._table_name is None:
            self._table_name = self.empty_model().table_name
        return self._table_name

    @property
    def configuration(self):
        return {
            'wheres': self.wheres,
            'sorts': self.sorts,
            'group_by_column': self.group_by_column,
            'joins': self.joins,
            'limit_start': self.limit_start,
            'limit_length': self.limit_length,
            'selects': self.selects,
            'table_name': self.get_table_name(),
            'model_columns': self._model_columns,
        }

    @configuration.setter
    def configuration(self, configuration):
        self.wheres = configuration['wheres']
        self.sorts = configuration['sorts']
        self.group_by_column = configuration['group_by_column']
        self.joins = configuration['joins']
        self.limit_start = configuration['limit_start']
        self.limit_length = configuration['limit_length']
        self.selects = configuration['selects']
        self._model_columns = configuration['model_columns']

    @property
    def table_name(self):
        """ Returns the name of the table for the model class """
        return self.model(None).table_name

    @property
    def model_columns(self):
        if self._model_columns is None:
            self._model_columns = self.empty_model().columns()
        return self._model_columns

    def select(self, selects):
        return self.clone().select_in_place(selects)

    def select_in_place(self, selects):
        self.selects = selects
        self.must_rexecute = True
        return self

    def where(self, where):
        """ Adds the given condition to the query and returns a new Models object """
        return self.clone().where_in_place(where)

    def where_in_place(self, where):
        """ Adds the given condition to the query for the current Models object """
        condition = self.parse_condition(where)
        self._validate_column(condition['column'], 'filter')
        self.wheres.append(self.parse_condition(where))
        self.must_rexecute = True
        self.must_recount = True
        return self

    def join(self, join):
        return self.clone().join_in_place(join)

    def join_in_place(self, join):
        self.joins.append(self.parse_join(join))
        self.must_rexecute = True
        self.must_recount = True
        return self

    def group_by(self, group_column):
        return self.clone().group_by_in_place(group_column)

    def group_by_in_place(self, group_column):
        self._validate_column(group_column, 'group')
        self.group_by_column = group_column
        self.must_rexecute = True
        self.must_recount = True
        return self

    def sort_by(self, primary_column, primary_direction, secondary_column=None, secondary_direction=None):
        return self.clone().sort_by_in_place(
            primary_column,
            primary_direction,
            secondary_column=secondary_column,
            secondary_direction=secondary_direction,
        )

    def sort_by_in_place(self, primary_column, primary_direction, secondary_column=None, secondary_direction=None):
        sorts = [
            { 'column': primary_column, 'direction': primary_direction },
            { 'column': secondary_column, 'direction': secondary_direction },
        ]
        sorts = filter(lambda sort: sort['column'] is not None and sort['direction'] is not None, sorts)
        self.sorts = list(map(lambda sort: self._normalize_and_validate_sort(sort), sorts))
        if len(self.sorts) == 0:
            raise ValueError('Missing primary column or direction in call to sort_by')
        self.must_rexecute = True
        return self

    def _normalize_and_validate_sort(self, sort):
        if 'column' not in sort or not sort['column']:
            raise ValueError("Missing 'column' for sort")
        if 'direction' not in sort or not sort['direction']:
            raise ValueError("Missing 'direction' for sort: should be ASC or DESC")
        direction = sort['direction'].upper().strip()
        if direction != 'ASC' and direction != 'DESC':
            raise ValueError(f"Invalid sort direction: should be ASC or DESC, not '{direction}'")
        self._validate_column(sort['column'], 'sort')

        # down the line we may ask the model class what columns we can sort on, but we're good for now
        return { 'column': sort['column'], 'direction': sort['direction'] }

    def _validate_column(self, column_name, action):
        """
        Down the line we may use the model configuration to check what columns are valid sort/group/search targets
        """
        # for now, only validate columns that belong to *our* table.
        column_name = column_name.replace('`', '')
        if '.' in column_name:
            parts = column_name.split('.')
            if parts[0] != self.get_table_name():
                return

            column_name = column_name.split('.')[1]
        model_columns = self.model_columns
        if column_name not in model_columns:
            model_class = self.model_class()
            raise KeyError(
                f"Cannot {action} by column '{column_name}' for model class {model_class.__name__} because this " + \
                'column does not exist for the model.  You can suppress this error by adding a matching column ' + \
                'to your model definition'
            )
        # if not self.model_class().has_column(column_name):
        #     raise ValueError(f'Invalid column {column_name}')

    def limit(self, start, length):
        return self.clone().limit_in_place(start, length)

    def limit_in_place(self, start, length):
        self.limit_start = start
        self.limit_length = length
        self.must_rexecute = True
        return self

    def find(self, where):
        """ Returns the first model where condition """
        return self.blank().where(where).first()

    def __len__(self):
        if self.must_recount:
            self.count = self._backend.count(self.configuration, self.empty_model())
            self.must_recount = False
        return self.count

    def __iter__(self):
        return iter([self.model(row) for row in self._backend.records(self.configuration, self.empty_model())])

    def model(self, data):
        model = self._build_model()
        model.data = data
        return model

    def _build_model(self):
        model_class = self.model_class()
        return model_class(self._backend, self._columns)

    def empty_model(self):
        return self.model({})

    def create(self, data):
        empty = self.empty_model()
        empty.save(data)
        return empty

    def first(self):
        iter = self.__iter__()
        try:
            return iter.__next__()
        except StopIteration:
            return self.empty_model()

    def columns(self, overrides=None):
        model = self.model({})
        return model.columns(overrides=None)
