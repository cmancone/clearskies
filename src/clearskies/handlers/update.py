from .write import Write
from .exceptions import InputError
from collections import OrderedDict
from ..functional import string
class Update(Write):
    def __init__(self, di):
        super().__init__(di)

    _configuration_defaults = {
        'model': None,
        'model_class': None,
        'columns': None,
        'writeable_columns': None,
        'readable_columns': None,
        'where': [],
        'input_error_callable': None,
    }

    def handle(self, input_output):
        input_data = self.request_data(input_output)
        external_id_column_name = self.auto_case_internal_column_name('id')
        if 'id' not in input_data:
            return self.error(input_output, f"Missing '{external_id_column_name}' in request body", 404)
        model_id = input_data['id']
        id_column_name = self.id_column_name
        models = self._model.where(f'{id_column_name}={model_id}')
        for where in self.configuration('where'):
            if type(where) == str:
                models = models.where(where)
            else:
                models = self._di.call_function(
                    where, models=models, input_output=input_output, routing_data=input_output.routing_data()
                )
        authorization = self._configuration.get('authorization', None)
        if authorization and hasattr(authorization, 'filter_models'):
            models = authorization.filter_models(models, input_output.get_authorization_data(), input_output)
        model = models.first()
        if not model.exists:
            return self.error(input_output, "Not Found", 404)
        del input_data['id']

        input_errors = {
            **self._extra_column_errors(input_data),
            **self._find_input_errors(model, input_data, input_output),
        }
        if input_errors:
            raise InputError(input_errors)
        model.save(input_data)

        return self.success(input_output, self._model_as_json(model, input_output))

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        error_prefix = 'Configuration error for %s:' % (self.__class__.__name__)
        if 'where' in configuration:
            if not hasattr(configuration['where'], '__iter__') or type(configuration['where']) == str:
                raise ValueError(
                    f"{error_prefix} 'where' should be an iterable of coditions or callables " + ", not " +
                    str(type(configuration['where'])),
                )
            for (index, where) in enumerate(configuration['where']):
                if type(where) != str and not callable(where):
                    raise ValueError(
                        f"{error_prefix} 'where' entry should be a string with a condition or a callable that filters models "
                        + f", but entry #{index+1} is neither of these",
                    )

    def documentation(self):
        nice_model = string.camel_case_to_words(self._model.__class__.__name__)
        id_label = 'id' if self.configuration('id_column_name') else self.id_column_name
        return self._documentation(
            description='Update the ' + nice_model + ' with an ' + id_label + ' of {' + id_label + '}',
            response_description=f'The updated {nice_model}',
            include_id_in_path=True,
        )
