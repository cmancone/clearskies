from abc import ABC, abstractmethod
from .condition_parser import ConditionParser


class Models(ABC, ConditionParser):
    # The database connection
    cursor = None
    conditions = None
    sorts = None
    parameters = None
    group_by_column = None
    limit_start = None
    limit_length = None
    must_rexecute = True

    def __init__(self, cursor):
        self.cursor = cursor
        self.conditions = []
        self.sorts = []
        self.parameters = []
        self.group_by_column = None
        self.joins = []
        self.limit_start = 0
        self.limit_length = None
        self.must_rexecute = True

    @property
    @abstractmethod
    def model_class(self):
        """ Return the model class that this models object will find/return instances of """
        pass

    def clone(self):
        clone = self.__class__(self.cursor)
        clone.configuration = self.configuration
        return clone

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

    def table_name(self):
        """ Returns the name of the table for the model class """
        return self.model_class().table_name

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
        return self

    def join(self, join):
        return self.clone().join_in_place(join)

    def join_in_place(self, join):
        if not 'join' in join.lower():
            raise ValueError("Invalid join string.  Should be '(LEFT|INNER|WHATEVER)? JOIN table ON condition'")
        self.joins.append(join)
        self.must_rexecute = True
        return self

    def group_by(self, group_column):
        return self.clone().group_by_in_place(group_column)

    def group_by_in_place(self, group_column):
        self._validate_column(group_column)
        self.group_by_column = group_column
        self.must_rexecute = True
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
        # if not self.model_class.has_column(column_name):
        #     raise ValueError(f'Invalid column {column_name}')

    def limit(self, start, length):
        return self.clone().limit_in_place(start, length)

    def limit_in_place(self, start, length):
        self.limit_start = start
        self.limit_length = length
        self.must_rexecute = True
        return self

    #def find(self, condition):
        #""" Returns the first model where {field}={value} """
        #return self.where(condition).first()
