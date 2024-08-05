from .requirement import Requirement


class MinimumValue(Requirement):
    minimum_value = None

    def configure(self, minimum_value):
        if type(minimum_value) != int:
            raise ValueError(
                f"Minimum value must be an int to use the MinimumValue class for column '{self.column_name}'"
            )
        self.minimum_value = minimum_value

    def check(self, model, data):
        if self.column_name not in data or not data[self.column_name]:
            return ""
        if int(data[self.column_name]) >= self.minimum_value:
            return ""
        return f"'{self.column_name}' must be at least {self.minimum_value}."
