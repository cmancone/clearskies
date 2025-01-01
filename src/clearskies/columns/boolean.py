from typing import Callable

import clearskies.typing
from clearskies import configs, parameters_to_properties, Model
from clearskies.column import Column
import clearskies.configs.actions


class Boolean(Column):
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
    default = configs.Boolean() #  type: ignore

    """
    A value to set for this column during a save operation.

    Unlike the default value, a setable value is always set during a save.
    """
    setable = configs.BooleanOrCallable() #  type: ignore

    """
    Actions to trigger when the column changes to True
    """
    on_true = clearskies.configs.actions.Actions(default=[])

    """
    Actions to trigger when the column changes to False
    """
    on_false = clearskies.configs.actions.Actions(default=[])

    @parameters_to_properties.parameters_to_properties
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

    def from_backend(self, instance, value) -> bool:
        if value == "0":
            return False
        return bool(value)

    def to_backend(self, data):
        if self.name not in data:
            return data

        return {**data, self.name: bool(data[self.name])}

    def __get__(self, instance, parent) -> bool | None:
        return super().__get__(instance, parent)

    def __set__(self, instance, value: bool) -> None:
        instance._next_data[self.name] = value

    def input_error_for_value(self, value: str, operator: str | None=None) -> str:
        return f"{self.name} must be a boolean" if type(value) != bool else ""

    def build_condition(self, value: str, operator: str | None=None, column_prefix: str=""):
        condition_value = "1" if value else "0"
        if not operator:
            operator = "="
        return f"{column_prefix}{self.name}{operator}{condition_value}"

    def save_finished(self, model: Model) -> None:
        """
        Make any necessary changes needed after a save has completely finished.
        """
        super().save_finished(model)

        if (not self.on_true and not self.on_false) or not model.was_changed(self.name):
            return

        if getattr(model, self.name) and self.on_true:
            self.execute_actions(self.on_true, model)
        if not getattr(model, self.name) and self.on_false:
            self.execute_actions(self.on_false, model)
