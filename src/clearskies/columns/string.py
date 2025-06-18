from __future__ import annotations

from typing import TYPE_CHECKING, Self, overload

from clearskies.column import Column

if TYPE_CHECKING:
    from clearskies import Model


class String(Column):
    """
    A simple string column.

    ```
    import clearskies


    class Pet(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Create(
            Pet,
            writeable_column_names=["name"],
            readable_column_names=["id", "name"],
        ),
    )
    wsgi()
    ```

    And when invoked:

    ```
    $ curl http://localhost:8080 -d '{"name": "Spot"}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "e5b8417f-91bc-4fe5-9b64-04f571a7b10a",
            "name": "Spot"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl http://localhost:8080 -d '{"name": 10}' | jq
    {
        "status": "input_errors",
        "error": "",
        "data": [],
        "pagination": {},
        "input_errors": {
            "name": "value should be a string"
        }
    }

    ```

    """

    _allowed_search_operators = ["<=>", "!=", "<=", ">=", ">", "<", "=", "in", "is not null", "is null", "like"]
    _descriptor_config_map = None

    @overload
    def __get__(self, instance: None, cls: type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: type[Model]) -> str:
        pass

    def __get__(self, instance, cls):
        if instance is None:
            self.model_class = cls
            return self

        if self.name not in instance._data:
            return None  # type: ignore

        if self.name not in instance._transformed_data:
            instance._transformed_data[self.name] = self.from_backend(instance._data[self.name])

        return instance._transformed_data[self.name]

    def __set__(self, instance: Model, value: str) -> None:
        instance._next_data[self.name] = value

    def input_error_for_value(self, value: str, operator: str | None = None) -> str:
        return "value should be a string" if type(value) != str else ""
