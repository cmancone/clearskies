from __future__ import annotations

from typing import TYPE_CHECKING

from clearskies.configs import config

if TYPE_CHECKING:
    from clearskies.schema import Schema as SchemaType


class Schema(config.Config):
    def __set__(self, instance, value: type[SchemaType]) -> None:
        if not hasattr(value, "get_columns"):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to parameter that requires a Schema."
            )
        instance._set_config(self, value)

    def __get__(self, instance, parent) -> type[SchemaType]:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
