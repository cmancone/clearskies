from .integer import Integer


class BelongsTo(Integer):
    """
    Controls a belongs to relationship.

    This column should be named something like 'parent_id', e.g. user_id, column_id, etc...  It expects the actual
    database column to be an integer.  It also provides an additional property on the model which returns the
    related model, instead of the id, with a name given by dropping `_id` from the column name.  In other words,
    if you have a column called user_id and a particular model has a user_id of 5, then:

    ```
    print(model.user_id)
    # prints 5
    print(model.user.id)
    # prints 5
    print(model.user.name)
    # prints the name of the user with an id of 5.
    ```
    """
    required_configs = [
        'parent_models_class',
    ]

    my_configs = [
        'parent_models',
    ]

    def __init__(self, di):
        self.di = di

    def configure(self, name, configuration, model_class):
        if 'parent_models_class' not in configuration:
            raise KeyError(
                f"Missing required configuration 'parent_models_class' for column '{name}' in model class " + \
                f"'{model_class.__name__}'"
            )

        # load up the parent models class now, because we'll need it in both the _check_configuration step
        # and can't load it there directly because we can't load it
        configuration['parent_models'] = self.di.build(configuration['parent_models_class'], cache=False)

        # continue normally now...
        super().configure(name, configuration, model_class)

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        if self.name[-3:] != '_id':
            raise ValueError(
                f"Invalid name for column '{self.name}' in '{self.model_class.__name__}' - " + \
                "BelongsTo column names must end in '_id'"
            )

    def _finalize_configuration(self, configuration):
        return {
            **super()._finalize_configuration(configuration),
            **{'model_column_name': self.name[:-3]}
        }

    def input_error_for_value(self, value):
        integer_check = super().input_error_for_value(value)
        if integer_check:
            return integer_check
        if not len(self.config('parent_models').where(f"id={value}")):
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
