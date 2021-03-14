from .column import Column


class Float(Column):
    def from_database(self, value):
        return float(value)

    def check_input(self, model, data):
        if not self.name in data:
            return ''
        if isinstance(data[self.name], int) or isinstance(data[self.name], float) or data[self.name] == None:
            return ''
        return f'Invalid input: {self.name} must be an integer or float'

    def build_condition(self, value, operator=None):
        if not operator:
            operator = '='
        return f"{self.name}{operator}{value}"

    def is_allowed_operator(self, operator):
        return operator in ['=', '<', '>', '<=', '>=']

    def input_error_for_value(self, value):
        return 'value should be an integer or float' if (type(value) != int and type(value) != float and value is not None) else ''
