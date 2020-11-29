from collections import OrderedDict


class Columns:
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
