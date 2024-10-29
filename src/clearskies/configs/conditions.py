from typing import Callable, List, Union

from clearskies.configs import config


class Conditions(config.Config):
    def __set__(self, instance, value: Union[str, Callable, List[Union[str, Callable]]]):
        if not isinstance(value, list):
            value = [value]

        for item, index in enumerate(value):
            if callable(item) or isinstance(item, str):
                continue

            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{item.__class__.__name__}' for item #{index+1} when a string or callable is required"
            )

        instance._set_config(self, value)

    def __get__(self, instance, parent) -> List[Union[str, Callable]]:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
