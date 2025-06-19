from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Self, overload

import clearskies.parameters_to_properties
import clearskies.typing
from clearskies import configs
from clearskies.autodoc.schema import Number as AutoDocNumber
from clearskies.autodoc.schema import Schema as AutoDocSchema
from clearskies.column import Column
from clearskies.query import Condition

if TYPE_CHECKING:
    from clearskies import Model


class Float(Column):
    """
    A column that stores a float.

    ```python
    import clearskies


    class MyModel(clearskies.Model):
        backend = clearskies.backends.MemoryBackend()
        id_column_name = "id"

        id = clearskies.columns.Uuid()
        score = clearskies.columns.Float()


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Create(
            MyModel,
            writeable_column_names=["score"],
            readable_column_names=["id", "score"],
        ),
        classes=[MyModel],
    )
    wsgi()
    ```

    and when invoked:

    ```bash
    $ curl 'http://localhost:8080' -d '{"score":15.2}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "7b5658a9-7573-4676-bf18-64ddc90ad87d",
            "score": 15.2
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080' -d '{"score":"15.2"}' | jq
    {
        "status": "input_errors",
        "error": "",
        "data": [],
        "pagination": {},
        "input_errors": {
            "score": "value should be an integer or float"
        }
    }
    ```
    """

    default = configs.Float()  #  type: ignore
    setable = configs.FloatOrCallable(default=None)  #  type: ignore
    _allowed_search_operators = ["<=>", "!=", "<=", ">=", ">", "<", "=", "in", "is not null", "is null"]
    auto_doc_class: type[AutoDocSchema] = AutoDocNumber
    _descriptor_config_map = None

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        default: float | None = None,
        setable: float | Callable[..., float] | None = None,
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
    def __get__(self, instance: Model, cls: type[Model]) -> float:
        pass

    def __get__(self, instance, cls):
        return super().__get__(instance, cls)

    def __set__(self, instance, value: float) -> None:
        instance._next_data[self.name] = float(value)

    def from_backend(self, value) -> float:
        return float(value)

    def to_backend(self, data):
        if self.name not in data or data[self.name] is None:
            return data

        return {**data, self.name: float(data[self.name])}

    def equals(self, value: float) -> Condition:
        return super().equals(value)

    def spaceship(self, value: float) -> Condition:
        return super().spaceship(value)

    def not_equals(self, value: float) -> Condition:
        return super().not_equals(value)

    def less_than_equals(self, value: float) -> Condition:
        return super().less_than_equals(value)

    def greater_than_equals(self, value: float) -> Condition:
        return super().greater_than_equals(value)

    def less_than(self, value: float) -> Condition:
        return super().less_than(value)

    def greater_than(self, value: float) -> Condition:
        return super().greater_than(value)

    def is_in(self, values: list[float]) -> Condition:
        return super().is_in(values)

    def input_error_for_value(self, value, operator=None):
        return (
            "value should be an integer or float"
            if (type(value) != int and type(value) != float and value is not None)
            else ""
        )
