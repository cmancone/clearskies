from .column import Column
class String(Column):
    def build_condition(self, value, operator=None):
        if operator and operator.lower() == 'like':
            return f"{self.name} LIKE '%{value}%'"
        return f"{self.name}={value}"

    def is_allowed_operator(self, operator):
        """
        This is called when processing user data to decide if the end-user is specifying an allowed operator
        """
        return operator == '=' or operator.lower() == 'like'

    def input_error_for_value(self, value, operator=None):
        return 'value should be a string' if type(value) != str else ''
