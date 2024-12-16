import json
from typing import Any, Callable

import clearskies.typing
from clearskies import parameters_to_properties
from clearskies.column import Column


class Json(Column):
    @parameters_to_properties.parameters_to_properties
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

    def __get__(self, instance, parent) -> dict[str, Any] | None:
        return super().__get__(instance, parent)

    def __set__(self, instance, value: dict[str, Any]) -> None:
        instance._next_data[self._my_name(instance)] = value

    def from_backend(self, instance, value) -> str:
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
