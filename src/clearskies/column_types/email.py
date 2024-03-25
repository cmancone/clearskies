from .string import String
import re


class Email(String):
    def __init__(self, di):
        super().__init__(di)

    def input_error_for_value(self, value, operator=None):
        if type(value) != str:
            return f"Value must be a string for {self.name}"
        if operator and operator.lower() == "like":
            # don't check for an email if doing a fuzzy search, since we may be searching
            # for a partial email
            return ""
        if re.search(r"^[^@\s]+@[^@]+\.[^@]+$", value):
            return ""
        return "Invalid email address"
