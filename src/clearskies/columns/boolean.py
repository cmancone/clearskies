from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Self, overload

import clearskies.configs.actions
import clearskies.parameters_to_properties
import clearskies.typing
from clearskies import configs
from clearskies.autodoc.schema import Boolean as AutoDocBoolean
from clearskies.autodoc.schema import Schema as AutoDocSchema
from clearskies.column import Column
from clearskies.query import Condition

if TYPE_CHECKING:
    from clearskies import Model


class Boolean(Column):
    """Represents a column with a true/false type."""

    """
    Actions to trigger when the column changes to True
    """
    on_true = clearskies.configs.actions.Actions(default=[])

    """
    Actions to trigger when the column changes to False
    """
    on_false = clearskies.configs.actions.Actions(default=[])

    """
    The class to use when documenting this column
    """
    auto_doc_class: type[AutoDocSchema] = AutoDocBoolean

    _allowed_search_operators = ["="]
    default = configs.Boolean()  #  type: ignore
    setable = configs.BooleanOrCallable()  #  type: ignore
    _descriptor_config_map = None

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        default: bool | None = None,
        setable: bool | Callable[..., bool] | None = None,
        is_readable: bool = True,
        is_writeable: bool = True,
        is_searchable: bool = True,
        is_temporary: bool = False,
        validators: clearskies.typing.validator | list[clearskies.typing.validator] = [],
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_true: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_false: clearskies.typing.action | list[clearskies.typing.action] = [],
        created_by_source_type: str = "",
        created_by_source_key: str = "",
        created_by_source_strict: bool = True,
    ):
        pass

    def from_backend(self, value) -> bool:
        if value == "0":
            return False
        return bool(value)

    def to_backend(self, data):
        if self.name not in data:
            return data

        return {**data, self.name: bool(data[self.name])}

    @overload
    def __get__(self, instance: None, cls: type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: type[Model]) -> bool:
        pass

    def __get__(self, instance, cls):
        return super().__get__(instance, cls)

    def __set__(self, instance, value: bool) -> None:
        instance._next_data[self.name] = value

    def input_error_for_value(self, value: str, operator: str | None = None) -> str:
        return f"{self.name} must be a boolean" if type(value) != bool else ""

    def build_condition(self, value: str, operator: str | None = None, column_prefix: str = ""):
        condition_value = "1" if value else "0"
        if not operator:
            operator = "="
        return f"{column_prefix}{self.name}{operator}{condition_value}"

    def save_finished(self, model: Model) -> None:
        """Make any necessary changes needed after a save has completely finished."""
        super().save_finished(model)

        if (not self.on_true and not self.on_false) or not model.was_changed(self.name):
            return

        if getattr(model, self.name) and self.on_true:
            self.execute_actions(self.on_true, model)
        if not getattr(model, self.name) and self.on_false:
            self.execute_actions(self.on_false, model)

    def equals(self, value: bool) -> Condition:
        return super().equals(value)
