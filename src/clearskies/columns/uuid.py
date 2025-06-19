from __future__ import annotations

from typing import TYPE_CHECKING, Any

import clearskies.di
import clearskies.parameters_to_properties
import clearskies.typing
from clearskies import configs
from clearskies.columns.string import String

if TYPE_CHECKING:
    from clearskies import Model


class Uuid(String):
    """
    Populates the column with a UUID upon record creation.

    This column really just has a very specific purpose: ids!

    When used, it will automatically populate the column with a random UUID upon record creation.
    It is not a writeable column, which means that you cannot expose it for write operations via an endpoint.

    ```python
    import clearskies


    class MyModel(clearskies.Model):
        backend = clearskies.backends.MemoryBackend()
        id_column_name = "id"

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Create(
            MyModel,
            writeable_column_names=["name"],
            readable_column_names=["id", "name"],
        ),
    )
    wsgi()
    ```

    and when invoked:

    ```bash
    $ curl http://localhost:8080 -d '{"name": "John Doe"}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "d4f23106-b48a-4dc5-9bf6-df61f6ca54f7",
            "name": "John Doe"
        },
        "pagination": {},
        "input_errors": {}
    }
    ```
    """

    is_writeable = configs.Boolean(default=False)
    _descriptor_config_map = None

    uuid = clearskies.di.inject.Uuid()

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        is_readable: bool = True,
        is_searchable: bool = True,
        is_temporary: bool = False,
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
    ):
        pass

    def pre_save(self, data: dict[str, Any], model: Model) -> dict[str, Any]:
        if model:
            return data
        data = {**data, self.name: str(self.uuid.uuid4())}
        if self.on_change_pre_save:
            data = self.execute_actions_with_data(self.on_change_pre_save, model, data)
        return data
