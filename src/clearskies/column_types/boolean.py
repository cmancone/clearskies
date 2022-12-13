from .column import Column
from ..autodoc.schema import Boolean as AutoDocBoolean
class Boolean(Column):
    _auto_doc_class = AutoDocBoolean

    def to_backend(self, data):
        if self.name not in data or data[self.name] is None:
            return data

        return {
            **data,
            self.name: bool(data[self.name]),
        }

    def from_backend(self, value):
        return bool(value)

    def input_error_for_value(self, value, operator=None):
        return f'{self.name} must be a boolean' if type(value) != bool else ''

    def build_condition(self, value, operator=None, column_prefix=''):
        condition_value = '1' if value else '0'
        if not operator:
            operator = '='
        return f"{column_prefix}{self.name}{operator}{condition_value}"
