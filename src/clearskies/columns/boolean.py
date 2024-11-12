from typing import Callable

import clearskies.typing
from clearskies import column_config


class Boolean(column_config.ColumnConfig):
    """
    Represents a column with a true/false type.

    By default, this column converts its value to 1/0 for compatibility with the most number
    of backends, so for SQL you can use a `TINYINT(1)` type.
    """

    """
    A default value to set for this column.

    The default is only used when creating a record for the first time, and only if
    a value for this column has not been set.
    """
    default = configs.Boolean()

    """
    A value to set for this column during a save operation.

    Unlike the default value, a setable value is always set during a save.
    """
    setable = configs.BooleanOrCallable()

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        default: bool | None = None,
        setable: bool| Callable[..., bool] | None = None,
        is_readable: bool = True,
        is_writeable: bool = True,
        is_temporary: bool = False,
        validators: clearskies.typing.validators | list[clearskies.typing.validators] = [],
        on_change_pre_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_post_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_save_finished: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        created_by_source_type: str = "",
        created_by_source_key: str = "",
    ):
        pass

    def __get__(self, instance, parent) -> bool:
        if not instance:
            return self  # type: ignore

        return instance._data[self._my_name(instance)]

    def __set__(self, instance, value: str) -> bool:
        instance._next_data[self._my_name(instance)] = value
