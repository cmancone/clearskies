from collections import OrderedDict, Sequence
import inspect


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
            configuration = {
                **configuration,
                'input_requirements':
                    self._resolve_input_requirements(configuration['input_requirements'], name, model_class.__name__)
                    if 'input_requirements' in configuration
                    else []
            }
            columns[name] = self.build_column(name, configuration, model_class)
        return columns

    def build_column(self, name, configuration, model_class):
        if not 'class' in configuration:
            raise ValueError(f"Missing column class for column {name} in {model_class.__name__}")
        column = self.object_graph.provide(configuration['class'])
        column.configure(name, configuration, model_class)
        return column

    def _resolve_input_requirements(self, input_requirements, column_name, model_class_name):
        error_prefix = f"Configuration error for column '{column_name}' in model '{model_class_name}':"
        if not hasattr(input_requirements, '__iter__'):
            raise ValueError(
                f"{error_prefix} 'input_requirements' should be an iterable but is {type(input_requirements)}"
            )
        resolved_requirements = []
        for (order, requirement) in enumerate(input_requirements, start=1):
            requirement_class = None
            args = []
            if inspect.isclass(requirement):
                requirement_class = requirement
            elif isinstance(requirement, Sequence) and type(requirement) != str:
                if not inspect.isclass(requirement[0]):
                    raise ValueError(
                        f"{error_prefix} incorrect value for input_requirement #{order}. First element should " +
                        f"be the Requirement class, but instead {type(input_requirement[0])} was found"
                    )
                requirement_class = requirement[0]
                args = requirement[1:]
            if requirement_class is None:
                raise ValueError(
                    f"{error_prefix} incorrect value for input_requirement #{order}. " +
                    f"It should be a Requirement class or a tuple/list, but it was {type(input_requirement)}"
                )
            requirement_instance = self.object_graph.provide(requirement_class)
            requirement_instance.column_name = column_name
            requirement_instance.configure(*args)
            resolved_requirements.append(requirement_instance)
        return resolved_requirements
