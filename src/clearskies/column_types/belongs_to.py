import re
from .string import String
from ..autodoc.schema import Array as AutoDocArray
from ..autodoc.schema import Object as AutoDocObject
from ..autodoc.schema import String as AutoDocString
from collections import OrderedDict
class BelongsTo(String):
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
    wants_n_plus_one = True
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
            parent_columns = self.di.build(configuration['parent_models_class'], cache=True).raw_columns_configuration()
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
        return {**super()._finalize_configuration(configuration), **{'model_column_name': self.name[:-3]}}

    def input_error_for_value(self, value, operator=None):
        integer_check = super().input_error_for_value(value)
        if integer_check:
            return integer_check
        parent_models = self.parent_models
        id_column_name = parent_models.get_id_column_name()
        if not len(parent_models.where(f"{id_column_name}={value}")):
            return f'Invalid selection for {self.name}: record does not exist'
        return ''

    def can_provide(self, column_name):
        return column_name == self.config('model_column_name')

    def provide(self, data, column_name):
        # did we have data parent data loaded up with a query?
        parent_table = self.parent_models.table_name()
        parent_id_column_name = self.parent_models.get_id_column_name()
        if f'{parent_table}_{parent_id_column_name}' in data:
            parent_data = {parent_id_column_name: data[f'{parent_table}_{parent_id_column_name}']}
            for column_name in self.parent_columns.keys():
                select_alias = f'{parent_table}_{column_name}'
                parent_data[column_name] = data[select_alias] if select_alias in data else None
            return self.parent_models.model(parent_data)

        # if not, just look it up from the id
        parent_id = data.get(self.name)
        if parent_id:
            parent_id_column_name = self.parent_models.get_id_column_name()
            return self.parent_models.where(f"{parent_id_column_name}={parent_id}").first()
        return self.parent_models.empty_model()

    def configure_n_plus_one(self, models, columns=None):
        if columns is None:
            columns = self.config('readable_parent_columns', silent=True)
        if not columns:
            return models

        own_table_name = models.table_name()
        parent_table = self.parent_models.table_name()
        parent_id_column_name = self.parent_models.get_id_column_name()
        with_join = models.join(
            f'{parent_table} on {parent_table}.{parent_id_column_name}={own_table_name}.{self.name}'
        )

        select_parts = [f'{parent_table}.{column_name} AS {parent_table}_{column_name}' for column_name in columns]
        select_parts.append(f'{parent_table}.{parent_id_column_name} AS {parent_table}_{parent_id_column_name}')
        return models.select(', '.join(select_parts))

    @property
    def parent_models(self):
        return self.di.build(self.config('parent_models_class'), cache=True)

    @property
    def parent_columns(self):
        return self.parent_models.model_columns

    def to_json(self, model):
        # if we don't have readable parent columns specified, then just return the id
        if not self.config('readable_parent_columns', silent=True):
            return super().to_json(model)

        # otherwise return an object with the readable parent columns
        columns = self.parent_columns
        parent = model.__getattr__(self.config('model_column_name'))
        json = OrderedDict()
        if parent.id_column_name not in self.config('readable_parent_columns'):
            json[parent.id_column_name] = columns[parent.id_column_name].to_json(parent)
        for column_name in self.config('readable_parent_columns'):
            column_data = columns[column_name].to_json(parent)
            if type(column_data) == dict:
                json = {**json, **column_data}
            else:
                json[column_name] = column_data

            json[column_name] = columns[column_name].to_json(parent)
        id_less_name = self.name[:-3]
        return {
            self.name: super().to_json(model),
            id_less_name: json,
        }

    def documentation(self, name=None, example=None, value=None):
        columns = self.parent_columns
        parent_id_column_name = self.parent_models.get_id_column_name()
        parent_properties = [columns[parent_id_column_name].documentation()]

        parent_columns = self.config('readable_parent_columns', silent=True)
        parent_id_doc = AutoDocString(name if name is not None else self.name)
        if not parent_columns:
            return parent_id_doc

        for column_name in self.config('readable_parent_columns'):
            if column_name == parent_id_column_name:
                continue
            parent_properties.append(columns[column_name].documentation())

        return [parent_id_doc, AutoDocObject(
            self.name[:-3],
            parent_properties,
        )]
