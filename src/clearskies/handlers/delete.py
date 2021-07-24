from collections import OrderedDict
from .base import Base
from .. import autodoc


class Delete(Base):
    _models = None

    _configuration_defaults = {
        'models': None,
        'models_class': None,
        'resource_id': None,
    }

    def __init__(self, di):
        super().__init__(di)

    def handle(self, input_output):
        input_data = input_output.request_data()
        resource_id = None
        if self.configuration('resource_id'):
            resource_id = self.configuration('resource_id')
        elif 'id' in input_data:
            resource_id = input_data['id']
        if not resource_id:
            return self.error(input_output, "Missing 'id'", 404)
        resource_id = int(resource_id)
        model = self._models.find(f'id={resource_id}')
        if not model.exists:
            return self.error(input_output, "Not Found", 404)

        model.delete()
        return self.success(input_output, {})

    def _check_configuration(self, configuration):
        error_prefix = 'Configuration error for %s:' % (self.__class__.__name__)
        has_models_class = ('models_class' in configuration) and configuration['models_class'] is not None
        has_models = ('models' in configuration) and configuration['models'] is not None
        if not has_models and not has_models_class:
            raise KeyError(f"{error_prefix} you must specify 'models' or 'models_class'")
        if has_models and has_models_class:
            raise KeyError(f"{error_prefix} you specified both 'models' and 'models_class', but can only provide one")
        self._models = self._di.build(configuration['models_class']) if has_models_class else configuration['models']

    def documentation(self):
        nice_model = self.camel_to_nice(self._models.model_class().__name__)

        authentication = self.configuration('authentication')
        standard_error_responses = []
        if not getattr(authentication, 'is_public', False):
            standard_error_responses.append(self.documentation_access_denied_response())
            if getattr(authentication, 'can_authorize', False):
                standard_error_responses.append(self.documentation_unauthorized_response())

        return [
            autodoc.request.Request(
                'Delete the ' + nice_model + ' with an id of {id}',
                [
                    self.documentation_success_response(
                        autodoc.schema.Object('data', children=[]),
                        description=f'The {nice_model} was deleted',
                    ),
                    *standard_error_responses,
                    self.documentation_not_found(),
                ],
                relative_path='{id}',
            )
        ]
