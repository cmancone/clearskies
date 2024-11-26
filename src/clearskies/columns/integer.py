from typing import Callable

import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.column import Column


class Integer(Column):
    """
    A column that stores integer data
    """

    """
    A default value to set for this column.

    The default is only used when creating a record for the first time, and only if
    a value for this column has not been set.
    """
    default = configs.Integer(default=None)

    """
    A value to set for this column during a save operation.

    Unlike the default value, a setable value is always set during a save.
    """
    setable = configs.IntegerOrCallable(default=None)

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        default: int | None = None,
        setable: int | Callable[..., int] | None = None,
        is_readable: bool = True,
        is_writeable: bool = True,
        is_temporary: bool = False,
        validators: clearskies.typing.validator | list[clearskies.typing.validator] = [],
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
        created_by_source_type: str = "",
        created_by_source_key: str = "",
        created_by_source_strict: bool = True,
    ):
        pass

    def __get__(self, instance, parent) -> int:
        if not instance:
            return self  # type: ignore

        return instance._data[self._my_name(instance)]

    def __set__(self, instance, value: int) -> None:
        instance._next_data[self._my_name(instance)] = value