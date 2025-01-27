from __future__ import annotations
from typing import overload, Self, TYPE_CHECKING, Type

from clearskies.column import Column

if TYPE_CHECKING:
    from clearskies import Model

class String(Column):
    """
    A simple string column
    """
    _allowed_search_operators = ["<=>", "!=", "<=", ">=", ">", "<", "=", "in", "is not null", "is null", "like"]

    @overload
    def __get__(self, instance: None, parent: Type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, parent: Type[Model]) -> str:
        pass

    def __get__(self, instance, parent):
        if not instance:
            return self

        if self.name not in instance._data:
            return None # type: ignore

        if self.name not in instance._transformed_data:
            instance._transformed_data[self.name] = self.from_backend(instance, instance._data[self.name])

        return instance._transformed_data[self.name]

    def __set__(self, instance: Model, value: str) -> None:
        instance._next_data[self.name] = value

    def input_error_for_value(self, value: str, operator: str | None=None) -> str:
        return "value should be a string" if type(value) != str else ""
