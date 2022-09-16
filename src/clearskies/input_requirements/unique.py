from .requirement import Requirement
class Unique(Requirement):
    def check(self, model, data):
        # Unique is mildly tricky.  We obviously want to search the backend for the new value,
        # but we need to first skip this if our column is not being set, or if we're editing
        # the model and nothing is changing.
        if self.column_name not in data:
            return ''
        new_value = data[self.column_name]
        if model.exists and model.__getattr__(self.column_name) == new_value:
            return ''

        matching_model = model.find(f'{self.column_name}={new_value}')
        if matching_model.exists:
            return f"Invalid value for '{self.column_name}': the given value already exists, and must be unique."
        return ''
