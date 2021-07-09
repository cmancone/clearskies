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

    def __init__(self, di):
        self.di = di

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        self.validate_models_class(configuration['parent_models_class'])

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
        if not len(self.parent_models.where(f"id={value}")):
            return f'Invalid selection for {self.name}: record does not exist'
        return ''

    def can_provide(self, column_name):
        return column_name == self.config('model_column_name')

    def provide(self, data, column_name):
        model_column_name = self.config('model_column_name')
        if model_column_name not in data or not data[model_column_name]:
            return self.parent_models.where(f"id={data[self.name]}").first()
        return self.parent_models.empty_model()

    @property
    def parent_models(self):
        return self.di.build(self.config('parent_models_class'), cache=False)
