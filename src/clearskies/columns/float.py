from typing import Callable, overload, Self

import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.column import Column


class Float(Column):
    """
    A column that stores a float
    """

    """
    A default value to set for this column.

    The default is only used when creating a record for the first time, and only if
    a value for this column has not been set.
    """
    default = configs.Float() #  type: ignore

    """
    A value to set for this column during a save operation.

    Unlike the default value, a setable value is always set during a save.
    """
    setable = configs.FloatOrCallable(default=None) #  type: ignore

    _allowed_search_operators = ["<=>", "!=", "<=", ">=", ">", "<", "=", "in", "is not null", "is null"]

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        default: float | None = None,
        setable: float | Callable[..., float] | None = None,
        is_readable: bool = True,
        is_writeable: bool = True,
        is_searchable: bool = True,
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

    @overload
    def __get__(self, instance: None, parent: type) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, parent: type) -> float:
        pass

    def __get__(self, instance, parent) -> float:
        return super().__get__(instance, parent)

    def __set__(self, instance, value: float) -> None:
        instance._next_data[self.name] = value

    def from_backend(self, instance, value) -> float:
        return float(value)

    def to_backend(self, data):
        if self.name not in data or data[self.name] is None:
            return data

        return {**data, self.name: float(data[self.name])}

    def equals(self, value: float) -> Condition:
        super().equals(value)

    def spaceship(self, value: float) -> Condition:
        super().spaceship(value)

    def not_equals(self, value: float) -> Condition:
        super().not_equals(value)

    def less_than_equals(self, value: float) -> Condition:
        super().less_than_equals(value)

    def greater_than_equals(self, value: float) -> Condition:
        super().greater_than_equals(value)

    def less_than(self, value: float) -> Condition:
        super().less_than(value)

    def greater_than(self, value: float) -> Condition:
        super().greater_than(value)

    def is_in(self, values: list[float]) -> Condition:
        super().is_in(value)
