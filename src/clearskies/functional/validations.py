import inspect
from typing import Any


def is_model(to_check: Any) -> bool:
    """
    Return True/False to denote if the given value is a model instance.

    Uses ducktyping rather than checking the type, mostly to minimize the risk of circular imports
    """
    if not hasattr(to_check, "destination_name"):
        return False
    return True


def is_model_class(to_check: Any) -> bool:
    """Return True/False to denote if the given value is a model class."""
    return inspect.isclass(to_check) and is_model(to_check)


def is_model_class_reference(to_check: Any) -> bool:
    """Return True/False to denote if the given value is a reference to a model class."""
    if not hasattr(to_check, "get_model_class"):
        return False

    if inspect.isclass(to_check):
        to_check = to_check()
    return is_model_class(to_check.get_model_class())


def is_model_class_or_reference(to_check: Any, raise_error_message=False, strict=True) -> bool:
    """
    Return True/False to denote if the given value is a model class or a model reference.

    If strict is false, then it won't check that the model reference returns a model class.  This is often necessary during
    validation by configs as, otherwise, it tends to trigger circular dependency errors.
    """
    if not inspect.isclass(to_check):
        # for references we will accept either instances or classes
        if hasattr(to_check, "get_model_class"):
            return is_model_class(to_check.get_model_class()) if strict else True

        if raise_error_message:
            raise TypeError(
                f"I expected a model class or reference, but instead I received something of type '{to_check.__class__.__name__}'"
            )
        return False

    if is_model_class(to_check):
        return True

    if hasattr(to_check, "get_model_class"):
        if not strict:
            return True

        model_class = to_check().get_model_class()
        if is_model_class(model_class):
            return True
        if raise_error_message:
            raise TypeError(
                f"I expected a model class or reference.  I received a model reference of class '{to_check.__name__}', but when I fetched the model out of it, it gave me back something that wasn't a model.  Instead, I received something of type '{model_class.__name__}'"
            )

    if raise_error_message:
        raise TypeError(
            "I expected a model class or reference, but instead I received a class that was neither.  It had a type of '"
            + to_check.__class__.__name__
            + "'"
        )

    return False


def is_model_or_class(to_check: Any) -> bool:
    """Return True/False to denote if the given value is a model instance or model class."""
    return is_model(to_check) or is_model_class(to_check)
