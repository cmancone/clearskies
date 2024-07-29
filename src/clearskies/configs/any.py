from typing import Any
from . import config


class Any(config.Config):
    def __set__(self, instance, value: Any):
        instance._set_config(self, value)

    def __get__(self, instance, parent) -> Any:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
