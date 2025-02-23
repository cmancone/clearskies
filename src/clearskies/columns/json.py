from __future__ import annotations
import json
from typing import Any, Callable, overload, Self, TYPE_CHECKING, Type

import clearskies.typing
import clearskies.parameters_to_properties
from clearskies import configs
from clearskies.column import Column

if TYPE_CHECKING:
    from clearskies import Model

class Json(Column):
    is_searchable = configs.Boolean(default=False)
    _descriptor_config_map = None

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        default: dict[str, Any] | None = None,
        setable: dict[str, Any] | Callable[..., dict[str, Any]] | None = None,
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

    @overload
    def __get__(self, instance: None, cls: Type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: Type[Model]) -> dict[str, Any]:
        pass

    def __get__(self, instance, cls):
        return super().__get__(instance, cls)

    def __set__(self, instance, value: dict[str, Any]) -> None:
        instance._next_data[self.name] = value

    def from_backend(self, value) -> dict[str, Any] | list[Any] | None:
        if type(value) == list or type(value) == dict:
            return value
        if not value:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    def to_backend(self, data):
        if self.name not in data or data[self.name] is None:
            return data

        value = data[self.name]
        return {**data, self.name: value if isinstance(value, str) else json.dumps(value)}
