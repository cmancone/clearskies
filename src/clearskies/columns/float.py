from clearskies import column_config


class Float(column_config.ColumnConfig):
    def __get__(self, instance, parent) -> float:
        if not instance:
            return self  # type: ignore

        return instance._data[self._my_name(instance)]

    def __set__(self, instance, value: str) -> float:
        instance._next_data[self._my_name(instance)] = value
