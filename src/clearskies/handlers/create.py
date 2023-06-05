from .write import Write
from .exceptions import InputError
from collections import OrderedDict
from ..functional import string
import json
class Create(Write):
    def __init__(self, di, logging):
        super().__init__(di)
        self._logging = logging

    def handle(self, input_output):
        model = self._model.empty_model()
        input_data = self.request_data(input_output)
        self._logging.debug('Incoming request data: ' + json.dumps(input_data))
        input_errors = {
            **self._extra_column_errors(input_data),
            **self._find_input_errors(model, input_data, input_output),
        }
        if input_errors:
            self._logging.debug('Request rejected due to input errors: ' + json.dumps(input_errors))
            raise InputError(input_errors)
        model.save(input_data)

        return self.success(input_output, self._model_as_json(model, input_output))

    def documentation(self):
        nice_model = string.camel_case_to_words(self._model.__class__.__name__)
        return self._documentation(
            description=f'Create a new {nice_model}',
            response_description=f'The new {nice_model}',
        )
