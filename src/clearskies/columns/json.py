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

    def __get__(self, instance, parent) -> dict[str, Any]:
        if not instance:
            return self  # type: ignore

        return instance._data[self._my_name(instance)]

    def __set__(self, instance, value: dict[str, Any]) -> None:
        instance._next_data[self._my_name(instance)] = value
