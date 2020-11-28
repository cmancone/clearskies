from abc import ABC, abstractmethod
from .condition_parser import ConditionParser


class Models(ABC, ConditionParser):
    # The database connection
    _cursor = None
    _columns = None
    conditions = None
    sorts = None
    parameters = None
    group_by_column = None
    limit_start = None
    limit_length = None
    select = None
    must_rexecute = True
    must_recount = True
    count = None

    def __init__(self, cursor, columns):
        self._cursor = cursor
        self._columns = columns
        self.conditions = []
        self.sorts = []
        self.parameters = []
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
        clone = self._blank()
        clone.configuration = self.configuration
        return clone

    def _blank(self):
        return self.__class__(self._cursor, self._columns)

    @property
    def configuration(self):
        return {
            'conditions': self.conditions,
            'sorts': self.sorts,
            'parameters': self.parameters,
            'group_by_column': self.group_by_column,
            'joins': self.joins,
            'limit_start': self.limit_start,
            'limit_length': self.limit_length,
            'selects': self.selects,
        }

    @configuration.setter
    def configuration(self, configuration):
        self.conditions = configuration['conditions']
        self.sorts = configuration['sorts']
        self.parameters = configuration['parameters']
        self.group_by_column = configuration['group_by_column']
        self.joins = configuration['joins']
        self.limit_start = configuration['limit_start']
        self.limit_length = configuration['limit_length']
        self.selects = configuration['selects']

    @property
    def table_name(self):
        """ Returns the name of the table for the model class """
        return self.model(None).table_name

    def select(self, selects):
        return self.clone().select_in_place(selects)

    def select_in_place(self, selects):
        self.selects = selects
        self.must_rexecute = True
        return self

    def where(self, condition):
        """ Adds the given condition to the query and returns a new Models object """
        return self.clone().where_in_place(condition)

    def where_in_place(self, condition):
        """ Adds the given condition to the query for the current Models object """
        condition_data = self.parse_condition(condition)
        self._validate_column(condition_data['column'])
        self.conditions.append(condition_data['parsed'])
        self.parameters.extend(condition_data['values'])
        self.must_rexecute = True
        self.must_recount = True
        return self

    def join(self, join):
        return self.clone().join_in_place(join)

    def join_in_place(self, join):
        if not 'join' in join.lower():
            raise ValueError("Invalid join string.  Should be '(LEFT|INNER|WHATEVER)? JOIN table ON condition'")
        self.joins.append(join)
        self.must_rexecute = True
        self.must_recount = True
        return self

    def group_by(self, group_column):
        return self.clone().group_by_in_place(group_column)

    def group_by_in_place(self, group_column):
        self._validate_column(group_column)
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
        self._validate_column(sort['column'])

        # down the line we may ask the model class what columns we can sort on, but we're good for now
        return { 'column': sort['column'], 'direction': sort['direction'] }

    def _validate_column(self, column_name):
        """
        Down the line we may use the model configuration to check what columns are valid sort/group/search targets
        """
        pass
        # if not self.model_class().has_column(column_name):
        #     raise ValueError(f'Invalid column {column_name}')

    def limit(self, start, length):
        return self.clone().limit_in_place(start, length)

    def limit_in_place(self, start, length):
        self.limit_start = start
        self.limit_length = length
        self.must_rexecute = True
        return self

    def find(self, condition):
        """ Returns the first model where condition """
        return self._blank().where(condition).first()

    def as_sql(self):
        select = self.selects if self.selects else '*'
        wheres = 'WHERE ' + ' AND '.join(self.conditions) if self.conditions else ''
        joins = ' '.join(self.joins)
        if self.sorts:
            order_by = 'ORDER BY ' + ', '.join(map(lambda sort: '%s %s' % (sort['column'], sort['direction']), self.sorts))
        else:
            order_by = ''
        group_by = 'GROUP BY ' + self.group_by_column if self.group_by_column else ''
        limit = f'LIMIT {self.limit_start}, {self.limit_length}' if self.limit_start else ''
        return f'SELECT {select} FROM {self.table_name} {joins} {wheres} {group_by} {order_by} {limit}'.strip()

    def as_count_sql(self):
        # note that this won't work if we start including a HAVING clause
        wheres = 'WHERE ' + ' AND '.join(self.conditions) if self.conditions else ''
        joins = ' '.join(filter(lambda join: 'LEFT JOIN' not in join, self.joins))
        if not self.group_by_column:
            return f'SELECT COUNT(*) AS count FROM {self.table_name} {joins} {wheres}'
        else:
            return f'SELECT COUNT(SELECT 1 FROM {self.table_name} {joins} {wheres} GROUP BY {self.group_by_column}) AS count'

    def __len__(self):
        if self.must_recount:
            self._cursor.execute(self.as_count_sql(), self.parameters)
            result = self._cursor.next()
            self.count = result[0] if type(result) == tuple else result['count']
            self.must_recount = False
        return self.count

    def __iter__(self):
        self._cursor.execute(self.as_sql(), self.parameters)
        return self

    def __next__(self):
        return self.model(self._cursor.next())

    def model(self, data):
        model_class = self.model_class()
        model = model_class(self._cursor, self._columns)
        model.data = data
        return model
