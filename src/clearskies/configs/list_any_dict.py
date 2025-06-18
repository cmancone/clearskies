from typing import Any

from clearskies.configs import config


class ListAnyDict(config.Config):
    def __set__(self, instance, value: list[dict[str, Any]]):
        if not isinstance(value, list):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to a parameter that requries a list."
            )
        for index, list_item in enumerate(value):
            if not isinstance(list_item, dict):
                error_prefix = self._error_prefix(instance)
                raise TypeError(
                    f"{error_prefix} I was expecting a list of dictionaries, but item # {index + 1} has type '{list_item.__class__.__name__}."
                )
            for key, val in list_item.items():
                if not isinstance(key, str):
                    error_prefix = self._error_prefix(instance)
                    raise TypeError(
                        f"{error_prefix} attempt to set a dictionary with a non-string key for item #{index + 1}."
                    )
        instance._set_config(self, value)

    def __get__(self, instance, parent) -> list[dict[str, Any]]:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
