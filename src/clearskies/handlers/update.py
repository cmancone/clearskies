from .write import Write
from .exceptions import InputError
from collections import OrderedDict


class Update(Write):
    def __init__(self, di):
        super().__init__(di)

    def handle(self, input_output):
        input_data = self.request_data(input_output)
        if 'id' not in input_data:
            return self.error(input_output, "Missing 'id' in request body", 404)
        model_id = int(input_data['id'])
        model = self._models.find(f'id={model_id}')
        if not model.exists:
            return self.error(input_output, "Not Found", 404)
        del input_data['id']

        input_errors = {
            **self._extra_column_errors(input_data),
            **self._find_input_errors(model, input_data),
        }
        if input_errors:
            raise InputError(input_errors)
        model.save(input_data)

        return self.success(input_output, self._model_as_json(model))

    def documentation(self):
        nice_model = self.camel_to_nice(self._models.model_class().__name__)
        return self._documentation(
            description='Update the ' + nice_model + ' with an id of {id}',
            response_description=f'The updated {nice_model}',
            include_id_in_path=True,
        )
