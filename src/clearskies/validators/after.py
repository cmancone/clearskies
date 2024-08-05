from .requirement import Requirement
import datetime
import dateparser


class After(Requirement):
    def configure(self, other_column_name: str, allow_equal: bool = False):
        self.other_column_name = other_column_name
        self.allow_equal = allow_equal

    def check(self, model, data):
        # we won't check anything for missing values (columns should be required if that is an issue)
        if not data.get(self.column_name):
            return ""
        my_value = data[self.column_name]
        other_value = data.get(self.other_column_name, model.__getitem__(self.other_column_name))
        # again, no checks for non-values
        if not other_value:
            return ""

        my_value_as_date = dateparser.parse(data[self.column_name])
        if not my_value_as_date:
            return f"'{self.column_name}' was not a valid date."

        if type(other_value) != str and type(other_value) != datetime.datetime:
            return f"'{other_column_name}' was not a valid date."
        other_value_as_date = dateparser.parse(other_value) if type(other_value) == str else other_value
        if not other_value_as_date:
            return f"'{self.other_column_name}' was not a valid date."

        if my_value_as_date == other_value_as_date:
            return "" if self.allow_equal else f"'{self.column_name}' must be after '{self.other_column_name}'"

        if my_value_as_date < other_value_as_date:
            return f"'{self.column_name}' must be after '{self.other_column_name}'"
        return ""
