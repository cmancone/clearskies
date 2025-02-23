from typing import Callable

from clearskies.configs import config


class Callable(config.Config):
    def __set__(self, instance, value: Callable):
        if not callable(value):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to a parameter that requries a Callable."
            )
        instance._set_config(self, value)

    def __get__(self, instance, parent) -> Callable:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
