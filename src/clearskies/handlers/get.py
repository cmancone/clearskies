from .base import Base
from collections import OrderedDict
from .. import autodoc
from .. import condition_parser
from ..functional import string


class Get(Base):
    _model = None

    _configuration_defaults = {
        'model': None,
        'model_class': None,
        'resource_id': None,
    }

    def __init__(self, di):
        super().__init__(di)

    def handle(self, input_output):
        model = self.fetch_model(input_output)
        if type(model) == str:
            return self.error(input_output, model, 404)
        return self.success(input_output, self._model_as_json(model))

    def fetch_model(self, input_output):
        input_data = input_output.request_data()
        resource_id = None
        if self.configuration('resource_id'):
            resource_id = self.configuration('resource_id')
        elif 'id' in input_data:
            resource_id = input_data['id']
        if not resource_id:
            return "Missing 'id'"
        model = self._model.find(f'{self.id_column_name}={resource_id}')
        if not model.exists:
            return "Not Found"

        return model

    def _check_configuration(self, configuration):
        error_prefix = 'Configuration error for %s:' % (self.__class__.__name__)
        has_model_class = ('model_class' in configuration) and configuration['model_class'] is not None
        has_model = ('model' in configuration) and configuration['model'] is not None
        if not has_model and not has_model_clas:
            raise KeyError(f"{error_prefix} you must specify 'model' or 'model_class'")
        if has_model and has_model_class:
            raise KeyError(f"{error_prefix} you specified both 'model' and 'model_class', but can only provide one")
        self._model = self._di.build(configuration['model_class']) if has_model_class else configuration['model']

    def documentation(self):
        nice_model = string.camel_case_to_words(self._model.__class__.__name__)

        authentication = self.configuration('authentication')
        standard_error_responses = []
        if not getattr(authentication, 'is_public', False):
            standard_error_responses.append(self.documentation_access_denied_response())
            if getattr(authentication, 'can_authorize', False):
                standard_error_responses.append(self.documentation_unauthorized_response())

        return [
            autodoc.request.Request(
                'Fetch the ' + nice_model + ' with an id of {id}',
                [
                    self.documentation_success_response(
                        autodoc.schema.Object(
                            'data',
                            children=self.documentation_data_schema(),
                            model_name=string.camel_case_to_words(self._model.__class__.__name__),
                        ),
                        description=f'The {nice_model} record',
                    ),
                    *standard_error_responses,
                    self.documentation_not_found(),
                ],
                relative_path='{id}',
            )
        ]

    def documentation_models(self):
        schema_model_name = string.camel_case_to_snake_case(self._model.__class__.__name__)

        return {
            schema_model_name: autodoc.schema.Object(
                'data',
                children=self.documentation_data_schema(),
            ),
        }
