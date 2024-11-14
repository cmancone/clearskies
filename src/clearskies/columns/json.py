from typing import Any

import clearskies.typing
from clearskies import parameters_to_properties
from clearskies.columns.column import Column


class Json(Column):
    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        default: dict[str, Any] | None = None,
        setable: dict[str, Any] | Callable[..., dict[str, Any]] | None = None,
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

    def __get__(self, instance, parent) -> dict[str, Any]:
        if not instance:
            return self  # type: ignore

        return instance._data[self._my_name(instance)]

    def __set__(self, instance, value: dict[str, Any]) -> None:
        instance._next_data[self._my_name(instance)] = value
