from clearskies.columns.string import String
import re


class Email(String):
    """
    A column that always requires an email address.
    """
    def input_error_for_value(self, value: str, operator: str | None=None) -> str:
        if type(value) != str:
            return f"Value must be a string for {self.name}"
        if operator and operator.lower() == "like":
            # don't check for an email if doing a fuzzy search, since we may be searching
            # for a partial email
            return ""
        if re.search(r"^[^@\s]+@[^@]+\.[^@]+$", value):
            return ""
        return "Invalid email address"
