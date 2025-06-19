from __future__ import annotations

from typing import TYPE_CHECKING

from clearskies.configs import config

if TYPE_CHECKING:
    from clearskies.column import Column


class Columns(config.Config):
    """This is for a configuration that should be a dictionary of columns with the key being the column name."""

    def __set__(self, instance, value: dict[str, Column]):
        if value is None:
            return

        if not isinstance(value, dict):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to a dictionary with columns"
            )
        for index, item in enumerate(value.values()):
            if not hasattr(item, "on_change_pre_save"):
                error_prefix = self._error_prefix(instance)
                raise TypeError(
                    f"{error_prefix} attempt to set a value of type '{item.__class__.__name__}' for item #{index + 1}.  A column was expected."
                )
        instance._set_config(self, value)

    def __get__(self, instance, parent) -> dict[str, Column]:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
