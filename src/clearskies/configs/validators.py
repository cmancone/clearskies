from typing import Callable, List, Union

from . import config
from clearskies.columns.validators.validator import Validator
from clearskies.bindings import Validator as BindingValidator


class Validators(config.Config):
    """
    A config that accepts various things that are accepted as validators in model columns:

     1. An instance of clearskies.columns.validators.Validator
     3. An instance of clearskies.bindings.Validator
     4. A list containing any combination of the above

    Incoming values are normalized to a list so that a list always comes out even if a non-list is provided.
    """

    def __set__(
        self, instance, value: Union[Callable, Validator, BindingValidator, List[Union[Callable, Validator, BindingValidator]]]
    ):
        if not isinstance(value, list):
            value = [value]

        for item, index in enumerate(value):
            if callable(item) or isinstance(item, Validator) or isinstance(item, BindingValidator):
                continue

            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{item.__class__.__name__}' for item #{index+1} when a callable, Validator, or BindingValidator is required"
            )

        instance._set_config(self, value)

    def __get__(self, instance, parent) -> List[Union[Callable, Validator, BindingValidator]]:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
