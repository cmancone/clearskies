from typing import Any, Callable

from clearskies.configs import config


class AnyDictOrCallable(config.Config):
    def __set__(self, instance, value: dict[str, Any] | Callable[..., dict[str, Any]]):
        if not isinstance(value, dict) and not callable(value):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to a parameter that requries a dictionary or a callable."
            )
        if isinstance(value, dict):
            for key, val in value.items():
                if not isinstance(key, str):
                    error_prefix = self._error_prefix(instance)
                    raise TypeError(f"{error_prefix} attempt to set a dictionary with a non-string key.")
        instance._set_config(self, value)

    def __get__(self, instance, parent) -> dict[str, Any] | Callable[..., dict[str, Any]]:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
