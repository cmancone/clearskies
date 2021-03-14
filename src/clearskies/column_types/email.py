from .string import String
from validate_email import validate_email


class Email(String):
    def input_error_for_value(self, value):
        if type(value) != str:
            return f'Value must be a string for {self.name}'
        if validate_email(
            email_address=value,
            check_blacklist=False,
            check_dns=False,
            check_smtp=False
        ):
            return ''
        return 'Invalid email address'
