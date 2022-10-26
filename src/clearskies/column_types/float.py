from .column import Column
from ..autodoc.schema import Number as AutoDocNumber
class Float(Column):
    _auto_doc_class = AutoDocNumber

    def from_backend(self, value):
        return float(value)

    def to_backend(self, data):
        if self.name not in data or data[self.name] is None:
            return data

        return {
            **data,
            self.name: float(data[self.name]),
        }

    def check_input(self, model, data):
        if not self.name in data:
            return ''
        if isinstance(data[self.name], int) or isinstance(data[self.name], float) or data[self.name] == None:
            return ''
        return f'Invalid input: {self.name} must be an integer or float'

    def build_condition(self, value, operator=None, column_prefix=''):
        if not operator:
            operator = '='
        return f"{column_prefix}{self.name}{operator}{value}"

    def is_allowed_operator(self, operator, relationship_reference=None):
        return operator in ['=', '<', '>', '<=', '>=']

    def input_error_for_value(self, value, operator=None):
        return 'value should be an integer or float' if (
            type(value) != int and type(value) != float and value is not None
        ) else ''
