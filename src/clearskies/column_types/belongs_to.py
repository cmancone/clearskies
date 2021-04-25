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

    When writeable via an API this expects to receive a simple id with the parent id, and will check that the
    given parent id exists before saving.  However, there is an additional mode of operation which you can enable
    by setting either (or both) of the 'can_create_parent' or 'can_update_parent' configuration keys to True.
    If you do this then you must also specify a list of column names from the parent model class which you would like
    to be writeable.  During an API call, the column will no longer expect an id to come up in `parent_id` column,
    but will instead expect a dictionary to come up in the 'parent' column, and will allow the client to
    update a parent record.  So, for instance, imagine a model with these column definitions:

    ```
    def columns_configuration(self):
        return OrderedDict([
            string('name'),
            belongs_to('user_id', parent_models_class=Users),
        ])
    ```

    Which is the standard mode of operation.  A valid API call would look like this:

    ```
    {
        "name": "Some Name",
        "user_id": 5,
    }
    ```

    But you could update the column to allow the end user to create/update the parent.  That would look like this:

    ```
    def columns_configuration(self):
        return OrderedDict([
            string('name'),
            belongs_to(
                'user_id',
                parent_models_class=Users,
                can_update_parent: True,
                writeable_parent_columns: ['username', 'email'],
            ),
        ])
    ```

    Assuming that the user model has columns named 'username' and 'email'.  Your API call could then look like this:

    ```
    {
        "id": 1,
        "name": "Some Name",
        "user": {
            "username": "myusername",
            "email": "myemail@example.com"
        }
    }
    ```

    And upon execution both the model would be updated (setting `name` to `Some Name`) and the username and email
    fields of the parent user model would be updated accordingly as well.  If this mode is enabled when creating
    a new record, then you must also provide the id of the parent when creating the record:

    ```
    {
        "id": 1,
        "name": "Some Name",
        "user": {
            "id": 5,
            "username": "myusername",
            "email": "myemail@example.com"
        }
    }
    ```
    """

    required_configs = [
        'parent_models_class',
    ]

    my_configs = [
        'can_update_parent',
        'writeable_parent_columns',
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

        # same with parent columns, except we'll only need those if can_update_parent is set.
        if configuration.get('can_update_parent'):
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
        if configuration.get('can_update_parent'):
            if not configuration.get('writeable_parent_columns'):
                raise ValueError(
                    f"To use 'can_update_parent' for a BelongsTo column you must also specify 'writeable_parent_columns'"
                )
            writeable_columns = configuration.get('writeable_parent_columns')
            if not hasattr(writeable_columns, '__iter__'):
                raise ValueError(
                    f"'writeable_parent_columns' must be an iterable but is not for column '{self.name}' " +
                    f"in model class '{self.model_class.__name__}'"
                )
            if isinstance(writeable_columns, str):
                raise ValueError(
                    f"'writeable_parent_columns' should be a list of column names but is a string for column " + \
                    f"'{self.name}' in model class '{self.model_class.__name__}'"
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
        if not 'can_update_parent' in configuration:
            configuration['can_update_parent'] = False
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

    def input_error_for_value(self, value):
        parent_models = self.config('parent_models')

        # if we can't write the parent model then
        if not self.config('can_update_parent'):
            check_integer = super().input_error_for_value(value)
            if check_integer:
                return check_integer
            if not len(parent_models.where(f'id={value}')):
                return f'Invalid value for {self.name}: id does not exist'
            return ''



        return ''
