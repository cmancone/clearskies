from .integer import Integer


class BelongsTo(Integer):
    required_configs = [
        'parent_models_class',
    ]

    my_configs = [
        'can_create',
        'writeable_columns',
        'parent_models',
        'parent_columns',
    ]

    def __init__(self, object_graph):
        self.object_graph = object_graph

    def configure(self, name, configuration, model_class):
        if 'parent_models_class' not in configuration:
            raise KeyError(
                f"Missing required configuration 'parent_models_class' for column '{name}' in model class " + \
                f"'{model_class.__name__}'"
            )

        # load up the parent models class now, because we'll need it in both the _check_configuration step
        # and can't load it there directly because we can't load it
        configuration['parent_models'] = self.object_graph.provide(configuration['parent_models_class'])

        # same with parent columns, except we'll only need those if can_create is set.
        if configuration.get('can_create'):
            configuration['parent_columns'] = configuration['parent_models'].columns()

        # continue normally now...
        super().configure(name, configuration, model_class)

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        if self.name[-3:] != '_id':
            raise ValueError(
                f"Invalid name for column '{self.name}' in '{self.model_class.__name__}' - " + \
                "BelongsTo column names must end in '_id'"
            )
        if configuration.get('can_create'):
            if not configuration.get('writeable_columns'):
                raise ValueError(
                    f"To use 'can_create' for a BelongsTo column you must also specify 'writeable_columns'"
                )
            writeable_columns = configuration.get('writeable_columns')
            if not hasattr(writeable_columns, '__iter__'):
                raise ValueError(
                    f"'writeable_columns' must be an iterable but is not for column '{self.name}' " +
                    f"in model class '{self.model_class.__name__}'"
                )
            if isinstance(writeable_columns, str):
                raise ValueError(
                    f"'writeable_columns' should be a list of column names but is a string for column '{self.name}'" + \
                    f" in model class '{self.model_class.__name__}'"
                )
            parent_columns = configuration['parent_columns']
            for column_name in writeable_columns:
                if column_name not in parent_columns:
                    raise KeyError(
                        f"Specified writeable column '{column_name}' in column '{self.name}' of model class " + \
                        f"'{self.model_class.__name__}' but the parent class, " + \
                        f"'{configuration['parent_models_class'].__name__}' does not have a column with that name"
                    )

    def _finalize_configuration(self, configuration):
        configuration = super()._finalize_configuration(configuration)
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
