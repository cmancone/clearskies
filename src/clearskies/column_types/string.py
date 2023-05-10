from .column import Column
class String(Column):
    def __init__(self, di):
        super().__init__(di)

    def build_condition(self, value, operator=None, column_prefix=''):
        if not operator:
            operator = '='
        if operator.lower() == 'like':
            return f"{column_prefix}{self.name} LIKE '%{value}%'"
        return f"{column_prefix}{self.name}{operator}{value}"

    def is_allowed_operator(self, operator, relationship_reference=None):
        """
        This is called when processing user data to decide if the end-user is specifying an allowed operator
        """
        if operator in ['=', '<', '>', '<=', '>=', 'in']:
            return True
        return operator.lower() == 'like'

    def input_error_for_value(self, value, operator=None):
        return 'value should be a string' if type(value) != str else ''
