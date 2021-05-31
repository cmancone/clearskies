from collections import OrderedDict, Sequence
import inspect
from .binding_config import BindingConfig


class Columns:
    def __init__(self, di):
        self.di = di

    def configure(self, definitions, model_class, overrides=None):
        columns = OrderedDict()
        for (name, configuration) in definitions.items():
            name = name.strip()
            if not name:
                raise ValueError(f"Missing name for column in '{model_class.__name__}'")
            if name in columns:
                raise ValueError(f"Duplicate column '{name}' found for model '{model_class.__name__}'")
            column_overrides = overrides[name] if (overrides is not None and name in overrides) else {}
            configuration = {
                **configuration,
                **column_overrides,
                'input_requirements': self._resolve_input_requirements(
                    self._merge_input_requirements(
                        configuration.get('input_requirements'),
                        column_overrides.get('input_requirements'),
                    ),
                    name,
                    model_class.__name__,
                )
            }
            columns[name] = self.build_column(name, configuration, model_class)

        # overrides can add columns too - need to handle those separately
        if overrides is not None:
            for (name, configuration) in overrides.items():
                if name in columns:
                    continue
                configuration['input_requirements'] = \
                    self._resolve_input_requirements(configuration['input_requirements'], name, model_class.__name__) \
                    if 'input_requirements' in configuration \
                    else []
                columns[name] = self.build_column(name, configuration, model_class)

        return columns

    def build_column(self, name, configuration, model_class):
        if not 'class' in configuration:
            raise ValueError(f"Missing column class for column {name} in {model_class.__name__}")
        column = self.di.build(configuration['class'], cache=False)
        column.configure(name, configuration, model_class)
        return column

    def _merge_input_requirements(self, config_requirements, override_requirements):
        if config_requirements is None and override_requirements is None:
            return []
        if config_requirements is None:
            return override_requirements
        if override_requirements is None:
            return config_requirements

        # if we have more than one of the same class then use the one from the overrides
        requirements = []
        used_classes = {}
        for requirement in override_requirements:
            requirements.append(requirement)
            [requirement_class, args, kwargs] = self._input_requirement_args_and_class(requirement)
            used_classes[requirement_class.__name__] = True
        for requirement in config_requirements:
            [requirement_class, args, kwargs] = self._input_requirement_args_and_class(requirement)
            if requirement_class.__name__ in used_classes:
                continue
            requirements.append(requirement)
            used_classes[requirement_class.__name__] = True

        return requirements

    def _input_requirement_args_and_class(self, requirement):
        """
        This takes the input requirement data provided by the developer and returns the things we need to build it.

        An input requirement can be:

         1. An InputRequirement class (aka `Required`)
         2. A tuple with the class and then configuration parameters for the class (aka `(MaxLength, 255)`)
         3. A BindingConfig

        This normalizes these three options and returns a list with `[Class, [args], {kwargs}]` for building
        """
        if inspect.isclass(requirement):
            return [requirement, [], {}]
        elif isinstance(requirement, BindingConfig):
            return [requirement.object_class, requirement.args, requirement.kwargs]
        elif isinstance(requirement, Sequence) and type(requirement) != str:
            if not inspect.isclass(requirement[0]):
                raise ValueError(
                    f"{error_prefix} incorrect value for input_requirement. First element should " +
                    f"be the Requirement class, but instead {type(requirement[0])} was found"
                )
            return [requirement[0], requirement[1:], {}]
        else:
            raise ValueError("Unrecognized value for input_requirement")

    def _resolve_input_requirements(self, input_requirements, column_name, model_class_name):
        error_prefix = f"Configuration error for column '{column_name}' in model '{model_class_name}':"
        if not hasattr(input_requirements, '__iter__'):
            raise ValueError(
                f"{error_prefix} 'input_requirements' should be an iterable but is {type(input_requirements)}"
            )
        resolved_requirements = []
        for requirement in input_requirements:
            [requirement_class, args, kwargs] = self._input_requirement_args_and_class(requirement)
            requirement_instance = self.di.build(requirement_class, cache=False)
            requirement_instance.column_name = column_name
            requirement_instance.configure(*args, **kwargs)
            resolved_requirements.append(requirement_instance)
        return resolved_requirements
