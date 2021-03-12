from .requirement import Requirement


class MaximumLength(Requirement):
    maximum_length = None

    def configure(self, *arguments):
        if len(arguments) < 1:
            raise ValueError(
                f"Must provide the maximum length to use the MaximumLength class for column '{self.column_name}'"
            )
        maximum_length = arguments[0]
        if type(maximum_length) != int:
            raise ValueError(
                f"Maximum length must be an int to use the MaximumLength class for column '{self.column_name}'"
            )
        self.maximum_length = maximum_length

    def check(self, model, data):
        if self.column_name not in data or not data[self.column_name]:
            return ''
        if len(data[self.column_name]) <= self.maximum_length:
            return ''
        return f"'{self.column_name}' must be at most {self.maximum_length} characters long."
