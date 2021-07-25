import re
from .integer import Integer
from ..autodoc.schema import Array as AutoDocArray
from ..autodoc.schema import Object as AutoDocObject
from ..autodoc.schema import Integer as AutoDocInteger


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
        'readable_parent_columns',
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

        if configuration.get('readable_parent_columns'):
            parent_columns = self.di.build(configuration['parent_models_class'], cache=False).raw_columns_configuration()
            error_prefix = f"Configuration error for '{self.name}' in '{self.model_class.__name__}':"
            readable_parent_columns = configuration['readable_parent_columns']
            if not hasattr(readable_parent_columns, '__iter__'):
                raise ValueError(
                    f"{error_prefix} 'readable_parent_columns' should be an iterable " + \
                    'with the list of child columns to output.'
                )
            if isinstance(readable_parent_columns, str):
                raise ValueError(
                    f"{error_prefix} 'readable_parent_columns' should be an iterable " + \
                    'with the list of child columns to output.'
                )
            for column_name in readable_parent_columns:
                if column_name not in parent_columns:
                    raise ValueError(
                        f"{error_prefix} 'readable_parent_columns' references column named '{column_name}' but this" + \
                        'column does not exist in the model class.'
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

    @property
    def parent_columns(self):
        return self.parent_models.model_columns

    def to_json(self, model):
        # if we don't have readable parent columns specified, then just return the id
        if not self.config('readable_parent_columns', silent=True):
            return super().to_json(model)

        # otherwise return an object with the readable parent columns
        columns = self.parent_columns
        parent = model.__getattr__(self.name)
        json = OrderedDict()
        if 'id' not in self.config('readable_parent_columns'):
            json['id'] = int(parent.id) if 'id' not in columns else columns['id'].to_json(parent)
        for column_name in self.config('readable_parent_columns'):
            json[column_name] = columns[column_name].to_json(parent)
        return json

    def documentation(self, name=None, example=None, value=None):
        columns = self.parent_columns
        parent_properties = [
            columns['id'].documentation() if ('id' in columns) else AutoDocInteger('id')
        ]

        parent_columns = self.config('readable_parent_columns', silent=True)
        if not parent_columns:
            return AutoDocInteger(name if name is not None else self.name)

        for column_name in self.config('readable_parent_columns'):
            if column_name == 'id':
                continue
            parent_properties.append(columns[column_name].documentation())

        return AutoDocObject(
            name if name is not None else self.name,
            parent_properties,
        )
