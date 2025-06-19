from __future__ import annotations

from typing import TYPE_CHECKING

from clearskies.configs import config

if TYPE_CHECKING:
    from clearskies import typing


class Validators(config.Config):
    """
    Validator config.

    A config that accepts various things that are accepted as validators in model columns:

     1. An instance of clearskies.validators.Validator
     2. A list of clearskies.validators.Validator

    Incoming values are normalized to a list so that a list always comes out even if a non-list is provided.
    """

    def __set__(
        self,
        instance,
        value: typing.validator | list[typing.validator],
    ):
        if not isinstance(value, list):
            value = [value]

        for index, item in enumerate(value):
            if hasattr(item, "additional_write_columns") and hasattr(item, "check"):
                continue

            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{item.__class__.__name__}' for item #{index + 1} when a Validator is required"
            )

        instance._set_config(self, [*value])

    def __get__(self, instance, parent) -> list[typing.validator]:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
