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

def is_model_class_reference(to_check: Any) -> bool:
    """
    Returns True/False to denote if the given value is a reference to a model class.
    """
    if not inspect.isclass(to_check)  or not hasattr(to_check, "get_model_class"):
        return False

    return is_model_class(to_check().get_model_class())

def is_model_class_or_reference(to_check: Any, raise_error_message=False) -> bool:
    """
    Returns True/False to denote if the given value is a model class or a model reference
    """
    if not inspect.isclass(to_check):
        if raise_error_message:
            raise TypeError("I expected a model class or reference, but instead I received something of type '" + type(to_check) + "'")
        return False

    if is_model_class(to_check):
        return True

    if hasattr(to_check, "get_model_class"):
        model_class = to_check().get_model_class()
        if is_model_class(model_class):
            return True
        if raise_error_message:
            raise TypeError("I expected a model class or reference.  I received a model reference of class '" + type(to_check) + "', but when I fetched the model out of it, it gave me back something that wasn't a model.  Instead, I received something of type '" + type(model_class) + "'")

    if raise_error_message:
        raise TypeError("I expected a model class or reference, but instead I received a class that was neither.  It had a type of '" + type(to_check) + "'")

    return False


def is_model_or_class(to_check: Any) -> bool:
    """
    Returns True/False to denote if the given value is a model instance or model class
    """
    return is_model(to_check) or is_model_class(to_check)
