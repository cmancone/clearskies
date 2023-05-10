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
        'model_column_name',
        'readable_parent_columns',
        'join_type',
    ]

    def __init__(self, di):
        super().__init__(di)

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        self.validate_models_class(configuration['parent_models_class'])

        if not configuration.get('model_column_name') and self.name[-3:] != '_id':
            raise ValueError(
                f"Invalid name for column '{self.name}' in '{self.model_class.__name__}' - " + \
                "BelongsTo column names must end in '_id', or you must set 'model_column_name' to specify the name of the column " + \
                "that the parent model can be fetched from."
            )
        if configuration.get('model_column_name') and type(configuration.get('model_column_name')) != str:
            raise ValueError(
                f"Configuration error for '{self.name}' in '{self.model_class.__name__}': 'model_column_name' must be a string."
            )

        join_type = configuration.get('join_type')
        if join_type and join_type.upper() not in ['LEFT', 'INNER']:
            raise ValueError(
                f"Configuration error for '{self.name}' in '{self.model_class.__name__}': join_type must be INNER or LEFT"
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
        return {
            **super()._finalize_configuration(configuration),
            **{
                'model_column_name':
                configuration.get('model_column_name') if configuration.get('model_column_name') else self.name[:-3],
                'join_type':
                configuration.get('join_type', 'INNER').upper(),
            }
        }

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
        alias = models.is_joined(parent_table)
        if not alias:
            alias = parent_table
            join_type = 'LEFT ' if self.config('join_type') == 'LEFT' else ''
            models = models.join(
                f'{join_type}JOIN {parent_table} on {parent_table}.{parent_id_column_name}={own_table_name}.{self.name}'
            )

        select_parts = [f'{alias}.{column_name} AS {parent_table}_{column_name}' for column_name in columns]
        select_parts.append(f'{alias}.{parent_id_column_name} AS {parent_table}_{parent_id_column_name}')
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
        id_less_name = self.config('model_column_name')
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
            self.config('model_column_name'),
            parent_properties,
        )]

    def is_allowed_operator(self, operator, relationship_reference=None):
        """
        This is called when processing user data to decide if the end-user is specifying an allowed operator
        """
        if not relationship_reference:
            return '='
        parent_columns = self.parent_columns
        if relationship_reference not in self.parent_columns:
            raise ValueError(
                "I was asked to search on a related column that doens't exist.  This shouldn't have happened :("
            )
        return self.parent_columns[relationship_reference].is_allowed_operator(operator)

    def check_search_value(self, value, operator=None, relationship_reference=None):
        if not relationship_reference:
            return self.input_error_for_value(value, operator=operator)
        parent_columns = self.parent_columns
        if relationship_reference not in self.parent_columns:
            raise ValueError(
                "I was asked to search on a related column that doens't exist.  This shouldn't have happened :("
            )
        return self.parent_columns[relationship_reference].check_search_value(value, operator=operator)

    def add_search(self, models, value, operator=None, relationship_reference=None):
        if not relationship_reference:
            return super().add_search(models, value, operator=operator)

        parent_columns = self.parent_columns
        if relationship_reference not in self.parent_columns:
            raise ValueError(
                "I was asked to search on a related column that doens't exist.  This shouldn't have happened :("
            )

        own_table_name = models.table_name()
        parent_table = self.parent_models.table_name()
        parent_id_column_name = self.parent_models.get_id_column_name()
        alias = models.is_joined(parent_table)
        if not alias:
            models = models.join(
                f'JOIN {parent_table} on {parent_table}.{parent_id_column_name}={own_table_name}.{self.name}'
            )
            alias = parent_table

        related_column = self.parent_columns[relationship_reference]
        return models.where(related_column.build_condition(value, operator=operator, column_prefix=f'{alias}.'))
