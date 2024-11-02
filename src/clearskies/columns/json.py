from typing import Any, Dict
from clearskies import column_config


class Json(column_config.ColumnConfig):
    def __get__(self, instance, parent) -> Dict[str, Any]:
        if not instance:
            return self  # type: ignore

        return instance._data[self._my_name(instance)]

    def __set__(self, instance, value: Dict[str, Any]) -> None:
        instance._next_data[self._my_name(instance)] = value
