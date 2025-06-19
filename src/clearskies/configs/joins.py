from __future__ import annotations

from typing import TYPE_CHECKING

from clearskies.configs import config

if TYPE_CHECKING:
    from clearskies import typing


class Joins(config.Config):
    def __set__(self, instance, value: typing.join | list[typing.join]):
        if not isinstance(value, list):
            value = [value]

        for index, item in enumerate(value):
            if callable(item) or isinstance(item, str):
                continue

            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{item.__class__.__name__}' for item #{index + 1} when a string or callable is required"  # type: ignore
            )

        instance._set_config(self, [*value])

    def __get__(self, instance, parent) -> list[typing.join]:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
