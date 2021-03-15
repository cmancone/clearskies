from collections import OrderedDict
from .base import Base


class Delete(Base):
    _models = None
    _object_graph = None

    _configuration_defaults = {
        'models': None,
        'models_class': None,
    }

    def __init__(self, input_output, authentication, object_graph):
        super().__init__(input_output, authentication)
        self._object_graph = object_graph

    def handle(self):
        input_data = self.json_body()
        if 'id' not in input_data:
            return self.error("Missing 'id' in request body", 404)
        model_id = int(input_data['id'])
        model = self._models.find(f'id={model_id}')
        if not model.exists:
            return self.error("Not Found", 404)

        model.delete()
        return self.success({})

    def _check_configuration(self, configuration):
        error_prefix = 'Configuration error for %s:' % (self.__class__.__name__)
        has_models_class = ('models_class' in configuration) and configuration['models_class'] is not None
        has_models = ('models' in configuration) and configuration['models'] is not None
        if not has_models and not has_models_class:
            raise KeyError(f"{error_prefix} you must specify 'models' or 'models_class'")
        if has_models and has_models_class:
            raise KeyError(f"{error_prefix} you specified both 'models' and 'models_class', but can only provide one")
        self._models = self._object_graph.provide(configuration['models_class']) if has_models_class else configuration['models']
