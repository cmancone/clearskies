from .column import Column


class Float(Column):
    def from_database(self, value):
        return float(value)

    def build_condition(self, value, operator=None):
        if not operator:
            operator = '='
        return f"{self.name}{operator}{value}"

    def is_allowed_operator(self, operator):
        return operator in ['=', '<', '>', '<=', '>=']

    def check_search_value(self, value):
        return 'value should be an integer or float' if (type(value) != int and type(value) != float) else ''
