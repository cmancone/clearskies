from .column import Column
from ..autodoc.schema import Integer as AutoDocInteger


class Integer(Column):
    _auto_doc_class = AutoDocInteger

    def from_backend(self, value):
        return int(value)

    def input_error_for_value(self, value, operator=None):
        if operator == 'in':
            if type(value) != list:
                return f'{self.name} must be an integer when searching with the "IN" operator'
            for val in value:
                if type(val) != int:
                    return f'All items in {self.name} must be integers'
            return ''
        return f'{self.name} must be an integer' if type(value) != int else ''

    def build_condition(self, value, operator=None):
        if operator == 'in':
            return f"{self.name} IN (" + ','.join([str(val) for val in value]) + ')'
        if not operator:
            operator = '='
        return f"{self.name}{operator}{value}"

    def is_allowed_operator(self, operator):
        return operator in ['=', '<', '>', '<=', '>=', 'in']
