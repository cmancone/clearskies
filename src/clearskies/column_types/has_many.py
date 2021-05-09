from .column import Column
import re
from collections import OrderedDict


class HasMany(Column):
    """
    Controls a has-many relationship.

    This is a readonly column.  When used in a model context it will return an iterable with the related child records.
    When used in an API context, it will convert the child records into a list of objects.

    It assumes that the foreign id in the child table is `[parent_model_class_name]_id` in all lower case.
    e.g., if the parent model class is named Status, then it assumes an id in the child class called `status_id`.
    """
    required_configs = [
        'child_models_class',
    ]

    my_configs = [
        'foreign_column_name',
        'child_models',
        'child_columns',
        'is_readable',
        'readable_child_columns',
    ]

    def __init__(self, object_graph):
        self.object_graph = object_graph

    @property
    def is_readable(self):
        is_readable = self.config('is_readable', True)
        # default is_readable to False
        return True if (is_readable and is_readable is not None) else False

    def configure(self, name, configuration, model_class):
        if 'child_models_class' not in configuration:
            raise KeyError(
                f"Missing required configuration 'child_models_class' for column '{name}' in model class " + \
                f"'{model_class.__name__}'"
            )

        # if readable_child_columns is set then load up the child models/columns now, because we'll need it in the
        # _check_configuration step, but we don't want to load it there because we can't save it back into the config
        if 'foreign_column_name' not in configuration:
            configuration['foreign_column_name'] = re.sub(
                r'(?<!^)(?=[A-Z])',
                '_',
                model_class.__name__.replace('_', '')
            ).lower() + '_id'
        if configuration.get('readable_child_columns'):
            configuration['child_models'] = self.object_graph.provide(configuration['child_models_class'])
            configuration['child_columns'] = configuration['child_models'].columns()

        # continue normally now...
        super().configure(name, configuration, model_class)

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        if configuration.get('is_readable'):
            error_prefix = f"Configuration error for '{self.name}' in '{self.model_class.__name__}':"
            if not 'readable_child_columns' in configuration:
                raise ValueError(f"{error_prefix} must provide 'readable_child_columns' if is_readable is set")
            readable_child_columns = configuration['readable_child_columns']
            if not hasattr(readable_child_columns, '__iter__'):
                raise ValueError(
                    f"{error_prefix} 'readable_child_columns' should be an iterable " + \
                    'with the list of child columns to output.'
                )
            if isinstance(readable_child_columns, str):
                raise ValueError(
                    f"{error_prefix} 'readable_child_columns' should be an iterable " + \
                    'with the list of child columns to output.'
                )
            for column_name in readable_child_columns:
                if column_name not in configuration['child_columns']:
                    raise ValueError(
                        f"{error_prefix} 'readable_child_columns' references column named '{column_name}' but this" + \
                        'column does not exist in the model class.'
                    )
                if not configuration['child_columns'][column_name].is_readable:
                    raise ValueError(
                        f"{error_prefix} 'readable_child_columns' references column named '{column_name}' but this" + \
                        'column is not readable.'
                    )

    def get_child_models(self):
        if 'child_models' not in self.configuration:
            self.configuration['child_models'] = self.object_graph.provide(self.config('child_models_class'))
        return self.configuration['child_models']

    def get_child_columns(self):
        if 'child_columns' not in self.configuration:
            self.configuration['child_columns'] = self.get_child_models().columns()
        return self.configuration['child_columns']

    def can_provide(self, column_name):
        return column_name == self.name

    def provide(self, data, column_name):
        foreign_column_name = self.config('foreign_column_name')
        return self.get_child_models().where(f"{foreign_column_name}={data['id']}")

    def to_json(self, model):
        children = []
        columns = self.get_child_columns()
        for child in model.__getattr__(self.name):
            json = OrderedDict()
            json['id'] = int(child.id)
            for column_name in self.config('readable_child_columns'):
                json[column_name] = columns[column_name].to_json(child)
            children.append(json)
        return children