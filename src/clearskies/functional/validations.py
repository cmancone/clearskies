from typing import Any
import inspect


def is_model(to_check: Any) -> bool:
    """
    Returns True/False to denote if the given value is a model instance

    Uses ducktyping rather than checking the type, mostly to minimize the risk of circular imports
    """
    if not hasattr(to_check, "destination_name"):
        return False
    if not hasattr(to_check, "column_configs"):
        return False
    return True


def is_model_class(to_check: Any) -> bool:
    """
    Returns True/False to denote if the given value is a model class
    """
    return inspect.isclass(to_check) and is_model(to_check)


def is_model_or_class(to_check: Any) -> bool:
    """
    Returns True/False to denote if the given value is a model instance or model class
    """
    return is_model(to_check) or is_model_class(to_check)
