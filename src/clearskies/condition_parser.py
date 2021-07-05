import re


class ConditionParser:
    operators = [
        '<=>',
        '!=',
        '<=',
        '>=',
        '>',
        '<',
        '=',
        'in',
        'is not null',
        'is null',
        'is not',
        'is',
        'like'
    ]

    operator_lengths = {
        '<=>': 3,
        '<=': 2,
        '>=': 2,
        '!=': 2,
        '>': 1,
        '<': 1,
        '=': 1,
        'in': 2,
        'is not null': 11,
        'is null': 7,
        'is not': 6,
        'is': 2,
        'like': 4,
    }

    operators_with_simple_placeholders = {
        '<=>': True,
        '<=': True,
        '>=': True,
        '!=': True,
        '=': True,
        '<': True,
        '>': True,
    }

    operators_without_placeholders = {
        'is not null',
        'is null',
    }

    def parse_condition(self, condition):
        lowercase_condition = condition.lower()
        matching_operator = None
        matching_index = len(condition)
        # figure out which operator comes earliest in the string: make sure and check all so we match the
        # earliest operator so we don't get weird results for things like 'age=name<=5'.
        for operator in self.operators:
            try:
                index = lowercase_condition.index(operator)
            except ValueError:
                continue
            if index < matching_index:
                matching_index = index
                matching_operator = operator

        if matching_operator is None:
            raise ValueError(f'No supported operators found in condition {condition}')

        column = condition[:matching_index].strip().replace('`', '')
        value = condition[matching_index+self.operator_lengths[matching_operator]:].strip()
        if value and (value[0] == "'" and value[-1] == "'"):
            value = value.strip("'")
        values = self._parse_condition_list(value) if matching_operator == 'in' else [value]
        table = ''
        if '.' in column:
            [table, column] = column.split('.')
        return {
            'table': table,
            'column': column,
            'operator': matching_operator.upper(),
            'values': [] if matching_operator in self.operators_without_placeholders else values,
            'parsed': self._with_placeholders(column, matching_operator, values)
        }

    def _parse_condition_list(self, value):
        if value[0] != '(' and value[-1] != ')':
            raise ValueError(f'Invalid search value {value} for condition.  For IN operator use `IN (value1,value2)`')

        # note: this is not very smart and will mess things up if there are single quotes/commas in the data
        return list(map(lambda value: value.strip().strip("'"), value[1:-1].split(',')))

    def _with_placeholders(self, column, operator, values):
        upper_case_operator = operator.upper()
        if operator in self.operators_with_simple_placeholders:
            return f'{column}{upper_case_operator}%s'
        if operator in self.operators_without_placeholders:
            return f'{column} {upper_case_operator}'
        if operator == 'is' or operator == 'is not' or operator == 'like':
            return f'{column} {upper_case_operator} %s'

        # the only thing left is "in" which has a variable number of placeholders
        return f'{column} IN (' + ', '.join(['%s' for i in range(len(values))]) + ')'

    def parse_join(self, join):
        # doing this the simple and stupid way, until that doesn't work.  Yes, it is ugly.
        # Splitting this into two regexps for simplicity: this one does not check for an alias
        matches = re.match(
            '(\w+\s+)?join\s+`?([^\s`]+)`?\s+on\s+`?([^`]+)`?\.`?([^`]+)`?\s*=\s*`?([^`]+)`?\.`?([^`]+)`?',
            join,
            re.IGNORECASE
        )
        if matches:
            groups = matches.groups()
            alias = ''
            join_type = groups[0]
            right_table = groups[1]
            first_table = groups[2]
            first_column = groups[3]
            second_table = groups[4]
            second_column = groups[5]
        else:
            matches = re.match(
                '(\w+\s+)?join\s+`?([^\s`]+)`?\s+(as\s+)?(\S+)\s+on\s+`?([^`]+)`?\.`?([^`]+)`?\s*=\s*`?([^`]+)`?\.`?([^`]+)`?',
                join,
                re.IGNORECASE
            )
            if not matches:
                raise ValueError(f"Specified join condition, '{join}' does not appear to be a valid join statement")
            groups = matches.groups()
            join_type = groups[0]
            right_table = groups[1]
            alias = groups[3]
            first_table = groups[4]
            first_column = groups[5]
            second_table = groups[6]
            second_column = groups[7]

        # which is the left table and which is the right table?
        match_by = alias if alias else right_table
        if first_table == match_by:
            join_data = {
                'left_table': second_table,
                'left_column': second_column,
                'right_table': first_table,
                'right_column': first_column,
            }
        elif second_table == match_by:
            join_data = {
                'left_table': first_table,
                'left_column': first_column,
                'right_table': second_table,
                'right_column': second_column,
            }
        else:
            raise ValueError(
                f"Specified join condition, '{join}' was not understandable because the joined table " + \
                "is not referenced in the 'on' clause"
            )

        return {
            **join_data,
            **{
                'type': groups[0].strip().upper() if groups[0] else 'INNER',
                'table': right_table,
                'alias': alias,
                'raw': join,
            }
        }
