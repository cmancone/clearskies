from typing import Callable

from clearskies.configs import config


class IntegerOrCallable(config.Config):
    def __set__(self, instance, value: int | Callable[..., int]):
        if not isinstance(value, int) and not callable(value):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to parameter that requires an integer or a callable."
            )
        instance._set_config(self, value)

    def __get__(self, instance, parent) -> int | Callable[..., int]:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
