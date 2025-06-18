import inspect

import wrapt  # type: ignore


@wrapt.decorator
def parameters_to_properties(wrapped, instance, args, kwargs):
    if not instance:
        raise ValueError(
            "The parameters_to_properties decorator only works for methods in classes, not plain functions"
        )

    if args:
        wrapped_args = inspect.getfullargspec(wrapped)
        for key, value in zip(wrapped_args.args[1:], args):
            # if it's a dictionary or a list then copy it to avoid linking data
            if isinstance(value, dict):
                value = {**value}
            if isinstance(value, list):
                value = [*value]
            setattr(instance, key, value)

    for key, value in kwargs.items():
        # if it's a dictionary or a list then copy it to avoid linking data
        if isinstance(value, dict):
            value = {**value}
        if isinstance(value, list):
            value = [*value]
        setattr(instance, key, value)

    wrapped(*args, **kwargs)
