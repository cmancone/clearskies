from typing import Any as AnyType

from clearskies.configs import config


class Any(config.Config):
    def __set__(self, instance, value: AnyType):
        instance._set_config(self, value)

    def __get__(self, instance, parent) -> AnyType:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
