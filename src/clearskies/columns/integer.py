from __future__ import annotations
from typing import Callable, overload, Self, TYPE_CHECKING, Type

import clearskies.typing
from clearskies import configs
import clearskies.parameters_to_properties
from clearskies.column import Column
from clearskies.query import Condition
from clearskies.autodoc.schema import Schema as AutoDocSchema
from clearskies.autodoc.schema import Integer as AutoDocInteger

if TYPE_CHECKING:
    from clearskies import Model

class Integer(Column):
    """
    A column that stores integer data
    """

    """
    A default value to set for this column.

    The default is only used when creating a record for the first time, and only if
    a value for this column has not been set.
    """
    default = configs.Integer(default=None) #  type: ignore

    """
    A value to set for this column during a save operation.

    Unlike the default value, a setable value is always set during a save.
    """
    setable = configs.IntegerOrCallable(default=None) #  type: ignore

    _allowed_search_operators = ["<=>", "!=", "<=", ">=", ">", "<", "=", "in", "is not null", "is null"]

    """
    The class to use when documenting this column
    """
    auto_doc_class: Type[AutoDocSchema] = AutoDocInteger

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        default: int | None = None,
        setable: int | Callable[..., int] | None = None,
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
    def __get__(self, instance: Model, parent: Type[Model]) -> int:
        pass

    def __get__(self, instance, parent):
        return int(super().__get__(instance, parent))

    def __set__(self, instance, value: int) -> None:
        instance._next_data[self.name] = value

    def from_backend(self, instance, value) -> int:
        return int(value)

    def to_backend(self, data):
        if self.name not in data or data[self.name] is None:
            return data

        return {**data, self.name: int(data[self.name])}

    def equals(self, value: int) -> Condition:
        return super().equals(value)

    def spaceship(self, value: int) -> Condition:
        return super().spaceship(value)

    def not_equals(self, value: int) -> Condition:
        return super().not_equals(value)

    def less_than_equals(self, value: int) -> Condition:
        return super().less_than_equals(value)

    def greater_than_equals(self, value: int) -> Condition:
        return super().greater_than_equals(value)

    def less_than(self, value: int) -> Condition:
        return super().less_than(value)

    def greater_than(self, value: int) -> Condition:
        return super().greater_than(value)

    def is_in(self, values: list[int]) -> Condition:
        return super().is_in(values)
