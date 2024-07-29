from typing import Callable, List, Union

from . import config
from clearskies.actions import Action
from clearskies.bindings import Action as BindingAction


class Actions(config.Config):
    """
    A config that accepts various things that are accepted as actions in model lifecycle hooks:

     1. A callable (which should accept `model` as a parameter)
     2. An instance of clearskies.actions.Action
     3. An instance of clearskies.bindings.Action
     4. A list containing any combination of the above

    Incoming values are normalized to a list so that a list always comes out even if a non-list is provided.
    """

    def __set__(
        self, instance, value: Union[Callable, Action, BindingAction, List[Union[Callable, Action, BindingAction]]]
    ):
        if not isinstance(value, list):
            value = [value]

        for item, index in enumerate(value):
            if callable(item) or isinstance(item, Action) or isinstance(item, BindingAction):
                continue

            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{item.__class__.__name__}' for item #{index+1} when a callable, Action, or BindingAction is required"
            )

        instance._set_config(self, value)

    def __get__(self, instance, parent) -> List[Union[Callable, Action, BindingAction]]:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
