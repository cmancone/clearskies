from typing import Callable

from clearskies import column_config


class Float(column_config.ColumnConfig):
    """
    A column that stores a float
    """

    """
    A default value to set for this column.

    The default is only used when creating a record for the first time, and only if
    a value for this column has not been set.
    """
    default = configs.Float()

    """
    A value to set for this column during a save operation.

    Unlike the default value, a setable value is always set during a save.
    """
    setable = configs.FloatOrCallable(default=None)

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        default: float | None = None,
        setable: float | Callable[..., float] | None = None,
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

    def __get__(self, instance, parent) -> float:
        if not instance:
            return self  # type: ignore

        return instance._data[self._my_name(instance)]

    def __set__(self, instance, value: str) -> float:
        instance._next_data[self._my_name(instance)] = value
