from __future__ import annotations

from typing import TYPE_CHECKING

from clearskies import action
from clearskies.configs import config

if TYPE_CHECKING:
    from clearskies import typing


class Actions(config.Config):
    """
    Action config.

    A config that accepts various things that are accepted as actions in model lifecycle hooks:

     1. A callable (which should accept `model` as a parameter)
     2. An instance of clearskies.actions.Action
     3. A list containing any combination of the above

    Incoming values are normalized to a list so that a list always comes out even if a non-list is provided.
    """

    def __set__(self, instance, value: typing.action | list[typing.action]):
        if not isinstance(value, list):
            value = [value]

        for index, item in enumerate(value):
            if callable(item) or isinstance(item, action.Action):
                continue

            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{item.__class__.__name__}' for item #{index + 1} when a callable or Action is required"
            )

        instance._set_config(self, [*value])

    def __get__(self, instance, parent) -> list[typing.action]:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
