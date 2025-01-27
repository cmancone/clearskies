from __future__ import annotations
from typing import Callable, overload, Self, TYPE_CHECKING, Type

import clearskies.typing
import clearskies.parameters_to_properties
from clearskies import configs
from clearskies.column import Column
from clearskies.query import Condition
from clearskies.autodoc.schema import Schema as AutoDocSchema
from clearskies.autodoc.schema import Number as AutoDocNumber

if TYPE_CHECKING:
    from clearskies import Model

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

    """
    The class to use when documenting this column
    """
    auto_doc_class: Type[AutoDocSchema] = AutoDocNumber

    @clearskies.parameters_to_properties.parameters_to_properties
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
    def __get__(self, instance: None, parent: Type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, parent: Type[Model]) -> float:
        pass

    def __get__(self, instance, parent):
        return float(super().__get__(instance, parent))

    def __set__(self, instance, value: float) -> None:
        instance._next_data[self.name] = value

    def from_backend(self, instance, value) -> float:
        return float(value)

    def to_backend(self, data):
        if self.name not in data or data[self.name] is None:
            return data

        return {**data, self.name: float(data[self.name])}

    def equals(self, value: float) -> Condition:
        return super().equals(value)

    def spaceship(self, value: float) -> Condition:
        return super().spaceship(value)

    def not_equals(self, value: float) -> Condition:
        return super().not_equals(value)

    def less_than_equals(self, value: float) -> Condition:
        return super().less_than_equals(value)

    def greater_than_equals(self, value: float) -> Condition:
        return super().greater_than_equals(value)

    def less_than(self, value: float) -> Condition:
        return super().less_than(value)

    def greater_than(self, value: float) -> Condition:
        return super().greater_than(value)

    def is_in(self, values: list[float]) -> Condition:
        return super().is_in(values)

    def input_error_for_value(self, value, operator=None):
        return (
            "value should be an integer or float"
            if (type(value) != int and type(value) != float and value is not None)
            else ""
        )
