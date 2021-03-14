from .integer import Integer


class BelongsTo(Integer):
    required_configs = [
        'parent_models_class'
    ]

    def __init__(self, object_graph):
        self.object_graph = object_graph

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        if self.name[-3:] != '_id':
            raise ValueError(
                f"Invalid name for column '{self.name}' in '{self.model_class.__name__}' - " + \
                "BelongsTo column names must end in '_id'"
            )

    def _finalize_configuration(self, configuration):
        configuration = super()._finalize_configuration(configuration)
        configuration['parent_models'] = self.object_graph.provide(configuration['parent_models_class'])
        configuration['model_column_name'] = self.name[:-3]
        return configuration

    def input_error_for_value(self, value):
        if not len(self.config('parent_models').where(f"{self.name}={value}")):
            return f'Invalid selection for {self.name}: record does not exist'
        return ''

    def can_provide(self, column_name):
        return column_name == self.config('model_column_name')

    def provide(self, data, column_name):
        model_column_name = self.config('model_column_name')
        models = self.config('parent_models')
        if model_column_name not in data or not data[model_column_name]:
            return models.where(f"{self.name}={data[self.name]}").first()
        return models.empty_model()
