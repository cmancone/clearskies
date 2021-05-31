from .write import Write
from .exceptions import InputError
from collections import OrderedDict


class Create(Write):
    def __init__(self, di):
        super().__init__(di)

    def handle(self, input_output):
        model = self._models.empty_model()
        input_data = self.request_data(input_output)
        input_errors = {
            **self._extra_column_errors(input_data),
            **self._find_input_errors(model, input_data),
        }
        if input_errors:
            raise InputError(input_errors)
        model.save(input_data)

        return self.success(input_output, self._model_as_json(model))
