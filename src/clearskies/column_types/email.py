from .string import String
import re


class Email(String):
    def input_error_for_value(self, value):
        if type(value) != str:
            return f'Value must be a string for {self.name}'
        if re.search('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$', value):
            return ''
        return 'Invalid email address'
