import wrapt
import inspect

from .column_config import ColumnConfig

from . import (
    # authentication,
    # autodoc,
    # backends,
    bindings,
    columns,
    configs,
    # contexts,
    # decorators,
    # di,
    functional,
    # handlers,
    # mocks,
    # secrets,
    # security_headers,
)

from .action import Action
from .model import Model
from .validator import Validator

# from .condition_parser import ConditionParser
# from .environment import Environment
# from .models import Models
# from .model import Model
# from .application import Application

@wrapt.decorator
def parameters_to_properties(wrapped, instance, args, kwargs):
    if not instance:
        raise ValueError("The parameters_to_properties decorator only works for methods in classes, not plain functions")

    if args:
        wrapped_args = inspect.getfullargspec(wrapped)
        for (key, value) in zip(wrapped_args.args[1:], args):
            setattr(instance, key, value)

    for (key, value) in kwargs.items():
        setattr(instance, key, value)

    wrapped(*args, **kwargs)

__all__ = [
    "Action",
    "bindings",
    "ColumnConfig",
    "columns",
    "configs",
    "functional",
    "Model",
    "parameters_to_properties",
    "Validator",
    # "authentication",
    # "autodoc",
    # "backends",
    # "column_types",
    # "contexts",
    # "decorators",
    # "di",
    # "functional",
    # "handlers",
    # "input_requirements",
    # "mocks",
    # "secrets",
    # "security_headers",
    # "ConditionParser",
    # "Environment",
    # "Application",
]
