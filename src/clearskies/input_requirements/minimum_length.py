from .requirement import Requirement


class MinimumLength(Requirement):
    minimum_length = None

    def configure(self, minimum_length):
        if type(minimum_length) != int:
            raise ValueError(
                f"Minimum length must be an int to use the MinimumLength class for column '{self.column_name}'"
            )
        self.minimum_length = minimum_length

    def check(self, model, data):
        # If the column isn't in the data then skip this check.  Otherwise, setting a minimum length would implicitly
        # make a column required, and this will likely cause more problems than it solves.  In short, the minimum
        # length should only apply if data is actually being set
        if self.column_name not in data or not data[self.column_name]:
            return ''
        if len(data[self.column_name]) >= self.minimum_length:
            return ''
        return f"'{self.column_name}' must be at least {self.minimum_length} characters long."
