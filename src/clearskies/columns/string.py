from clearskies.column import Column


class String(Column):
    """
    A simple string column
    """
    _allowed_search_operators = ["<=>", "!=", "<=", ">=", ">", "<", "=", "in", "is not null", "is null", "like"]

    @overload
    def __get__(self, instance: None, parent: type) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, parent: type) -> str:
        pass

    def __get__(self, instance: Model, parent: type):
        if not instance:
            return self

        if self.name not in instance._data:
            return None # type: ignore

        if self.name not in instance._transformed_data:
            instance._transformed_data[self.name] = self.from_backend(instance, instance._data[self.name])

        return instance._transformed_data[self.name]

    def __set__(self, instance: Model, value: str) -> None:
        instance._next_data[self.name] = value
