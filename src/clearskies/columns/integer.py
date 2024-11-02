from clearskies import column_config


class Integer(column_config.ColumnConfig):
    def __get__(self, instance, parent) -> int:
        if not instance:
            return self  # type: ignore

        return instance._data[self._my_name(instance)]

    def __set__(self, instance, value: int) -> None:
        instance._next_data[self._my_name(instance)] = value
