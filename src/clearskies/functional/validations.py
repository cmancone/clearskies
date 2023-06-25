from typing import Any
from .. import model
import inspect


def is_model(to_check: Any) -> bool:
    """
    Returns True/False to denote if the given value is a model instance
    """
    return isinstance(to_check, model.Model)


def is_model_class(to_check: Any) -> bool:
    """
    Returns True/False to denote if the given value is a model class
    """
    return inspect.isclass(to_check) and issubclass(to_check, model.Model)


def is_model_or_class(to_check: Any) -> bool:
    """
    Returns True/False to denote if the given value is a model instance or model class
    """
    return is_model(to_check) or is_model_class(to_check)
