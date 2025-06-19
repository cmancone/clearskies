from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Self, overload

import clearskies.parameters_to_properties
import clearskies.typing
from clearskies import configs
from clearskies.autodoc.schema import Integer as AutoDocInteger
from clearskies.autodoc.schema import Schema as AutoDocSchema
from clearskies.column import Column
from clearskies.query import Condition

if TYPE_CHECKING:
    from clearskies import Model


class Integer(Column):
    """
    A column that stores integer data.

    ```python
    import clearskies


    class MyModel(clearskies.Model):
        backend = clearskies.backends.MemoryBackend()
        id_column_name = "id"

        id = clearskies.columns.Uuid()
        age = clearskies.columns.Integer()


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Create(
            MyModel,
            writeable_column_names=["age"],
            readable_column_names=["id", "age"],
        ),
        classes=[MyModel],
    )
    wsgi()
    ```

    And when invoked:

    ```bash
    $ curl 'http://localhost:8080' -d '{"age":20}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "6ea74719-a65f-45ae-b6a3-641ce682ed25",
            "age": 20
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080' -d '{"age":"asdf"}' | jq
    {
        "status": "input_errors",
        "error": "",
        "data": [],
        "pagination": {},
        "input_errors": {
            "age": "value should be an integer"
        }
    }
    ```
    """

    default = configs.Integer(default=None)  #  type: ignore
    setable = configs.IntegerOrCallable(default=None)  #  type: ignore
    _allowed_search_operators = ["<=>", "!=", "<=", ">=", ">", "<", "=", "in", "is not null", "is null"]

    auto_doc_class: type[AutoDocSchema] = AutoDocInteger

    _descriptor_config_map = None

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        default: int | None = None,
        setable: int | Callable[..., int] | None = None,
        is_readable: bool = True,
        is_writeable: bool = True,
        is_searchable: bool = True,
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
    def __get__(self, instance: None, cls: type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: type[Model]) -> int:
        pass

    def __get__(self, instance, cls):
        if instance is None:
            self.model_class = cls
            return self

        value = super().__get__(instance, cls)
        return None if value is None else int(value)

    def __set__(self, instance, value: int) -> None:
        instance._next_data[self.name] = value

    def from_backend(self, value) -> int | None:
        return None if value is None else int(value)

    def to_backend(self, data):
        if self.name not in data or data[self.name] is None:
            return data

        return {**data, self.name: int(data[self.name])}

    def input_error_for_value(self, value, operator=None):
        try:
            int(value)
        except ValueError:
            return "value should be an integer"
        return ""

    def equals(self, value: int) -> Condition:
        return super().equals(value)

    def spaceship(self, value: int) -> Condition:
        return super().spaceship(value)

    def not_equals(self, value: int) -> Condition:
        return super().not_equals(value)

    def less_than_equals(self, value: int) -> Condition:
        return super().less_than_equals(value)

    def greater_than_equals(self, value: int) -> Condition:
        return super().greater_than_equals(value)

    def less_than(self, value: int) -> Condition:
        return super().less_than(value)

    def greater_than(self, value: int) -> Condition:
        return super().greater_than(value)

    def is_in(self, values: list[int]) -> Condition:
        return super().is_in(values)
