from .requirement import Requirement


class Required(Requirement):
    def check(self, model, data):
        # you'd think that "required" is straight forward and we want an input error if it isn't found.
        # this isn't strictly true though.  If the model already exists, the column has a value in the model already,
        # and the column is completely missing from the input data, then it is actually perfectly fine (because
        # there will still be a value in the column after the save).  However, if the model doesn't exist, then
        # we must require the column in the data with an actual value.
        has_value = False
        has_some_value = False
        if self.column_name in data:
            has_some_value = True
            if type(data[self.column_name]) == str:
                has_value = bool(data[self.column_name].strip())
            else:
                has_value = bool(data[self.column_name])
        if has_value:
            return ''
        if model.exists and model[self.column_name] and not has_some_value:
            return ''
        return f"'{self.column_name}' is required."
