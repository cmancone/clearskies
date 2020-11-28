from collections import OrderedDict


class Columns:
    """
    If True (the default) data for this column will be saved to the database assuming the same column name

    This should be disabled if the data can't just go directly in, for instance with a many-to-many relationship
    where it gets sent to a separate table.
    """
    def save_directly_to_database = True

    def __init__(self, object_graph):
        self.object_graph = object_graph

    def configure(self, definitions, model_class):
        columns = OrderedDict()
        for (name, configuration) in definitions.items():
            name = name.strip()
            if not name:
                raise ValueError(f"Missing name for column in '{model_class.__name__}'")
            if name in columns:
                raise ValueError(f"Duplicate column '{name}' found for model '{model_class.__name__}'")
            columns[name] = self.build_column(name, configuration, model_class)
        return columns

    def build_column(self, name, configuration, model_class):
        if not 'class' in configuration:
            raise ValueError(f"Missing column class for column {name} in {model_class.__name__}")
        column = self.object_graph.provide(configuration['class'])
        column.configure(name, configuration, model_class)
        return column
