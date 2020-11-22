class ConditionParser:
    operators = [
        '<=>',
        '<=',
        '>=',
        '!=',
        '=',
        'in',
        'is not null',
        'is null',
        'is not',
        'is',
    ]

    operator_lengths = {
        '<=>': 3,
        '<=': 2,
        '>=': 2,
        '!=': 2,
        '=': 1,
        'in': 2,
        'is not null': 11,
        'is null': 7,
        'is not': 6,
        'is': 2,
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
            except: ValueError:
                continue
            if index < matching_index:
                matching_index = index
                matching_operator = operator

        if matching_operator is None:
            raise ValueError(f'No supported operators found in condition {condition}')

        column = condition[:matching_index]
        value = condition[matching_index+self.operator_lengths[operator]:].strip()
        if value[0] == "'" and value[-1] == "'":
            value = value.strip("'")
        operator = operator.upper()
        return {
            'column': column,
            'operator': operator,
            'value': self.parse_condition_list(value) if operator == 'IN' else value
        }

    def parse_condition_list(self, value):
        ######### HERE!!!!!!! ###########
