from .write import Write
from .exceptions import InputError
from collections import OrderedDict
from ..functional import string
class Update(Write):
    def __init__(self, di):
        super().__init__(di)

    def handle(self, input_output):
        input_data = self.request_data(input_output)
        external_id_column_name = self.auto_case_internal_column_name('id')
        if 'id' not in input_data:
            return self.error(input_output, f"Missing '{external_id_column_name}' in request body", 404)
        model_id = input_data['id']
        id_column_name = self.id_column_name
        model = self._model.find(f'{id_column_name}={model_id}')
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
        nice_model = string.camel_case_to_words(self._model.__class__.__name__)
        return self._documentation(
            description='Update the ' + nice_model + ' with an id of {id}',
            response_description=f'The updated {nice_model}',
            include_id_in_path=True,
        )
