from typing import Callable

import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.columns.string import String


class Select(String):
    """
    A string column but, when writeable via an endpoint, only specific values are allowed.

    Note: the allowed values are case sensitive.

    ```python
    import clearskies


    class Order(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        total = clearskies.columns.Float()
        status = clearskies.columns.Select(["Open", "Processing", "Shipped", "Complete"])


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Create(
            Order,
            writeable_column_names=["total", "status"],
            readable_column_names=["id", "total", "status"],
        ),
    )
    wsgi()
    ```

    And when invoked:

    ```bash
    $ curl http://localhost:8080 -d '{"total": 125, "status": "Open"}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "22f2c950-6519-4d8e-9084-013455449b07",
            "total": 125.0,
            "status": "Open"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl http://localhost:8080 -d '{"total": 125, "status": "huh"}' | jq
    {
        "status": "input_errors",
        "error": "",
        "data": [],
        "pagination": {},
        "input_errors": {
            "status": "Invalid value for status"
        }
    }
    ```
    """

    """ The allowed values. """
    allowed_values = configs.StringList(required=True)
    _descriptor_config_map = None

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        allowed_values: list[str],
        default: str | None = None,
        setable: str | Callable[..., str] | None = None,
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

    def input_error_for_value(self, value: str, operator: str | None = None) -> str:
        return f"Invalid value for {self.name}" if value not in self.allowed_values else ""
