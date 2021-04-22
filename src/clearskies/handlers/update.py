from .write import Write
from .exceptions import InputError
from collections import OrderedDict


class Update(Write):
    def __init__(self, input_output, object_graph):
        super().__init__(input_output, object_graph)

    def handle(self):
        input_data = self.request_data()
        if 'id' not in input_data:
            return self.error("Missing 'id' in request body", 404)
        model_id = int(input_data['id'])
        model = self._models.find(f'id={model_id}')
        if not model.exists:
            return self.error("Not Found", 404)
        del input_data['id']

        input_errors = {
            **self._extra_column_errors(input_data),
            **self._find_input_errors(model, input_data),
        }
        if input_errors:
            raise InputError(input_errors)
        model.save(input_data)

        return self.success(self._model_as_json(model))
