from .requirement import Requirement


class MaximumValue(Requirement):
    maximum_value = None

    def configure(self, maximum_value):
        if type(maximum_value) != int:
            raise ValueError(
                f"Maximum value must be an int to use the MaximumValue class for column '{self.column_name}'"
            )
        self.maximum_value = maximum_value

    def check(self, model, data):
        if self.column_name not in data or not data[self.column_name]:
            return ""
        if int(data[self.column_name]) <= self.maximum_value:
            return ""
        return f"'{self.column_name}' must be at most {self.maximum_value}."
