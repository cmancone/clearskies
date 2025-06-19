from __future__ import annotations

from typing import TYPE_CHECKING, Any

import clearskies.parameters_to_properties
import clearskies.typing
from clearskies import configs
from clearskies.columns.string import String

if TYPE_CHECKING:
    from clearskies import Model


class CreatedByIp(String):
    """
    Return the ip address of the client when the record is created.

    If the ip address isn't available from the context being executed, then you may end up with an error
    (depending on the context).  This is a good thing if you are trying to consistely provide audit information,
    but may be a problem if your model creation needs to happen more flexibly.  Example:

    ```python
    import clearskies


    class MyModel(clearskies.Model):
        backend = clearskies.backends.MemoryBackend()
        id_column_name = "id"

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        ip_address = clearskies.columns.CreatedByIp()


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Create(
            MyModel,
            writeable_column_names=["name"],
            readable_column_names=["id", "name", "ip_address"],
        ),
        classes=[MyModel],
    )
    wsgi()
    ```

    And if you invoked this:

    ```bash
    $ curl 'http://localhost:8080' -d '{"name":"Bob"}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "62e457fe-1680-4fa1-b4e3-0329f304fedb",
            "name": "Bob",
            "ip_address": "127.0.0.1"
        },
        "pagination": {},
        "input_errors": {}
    }

    ```
    """

    """
    Since this column is always populated automatically, it is never directly writeable.
    """
    is_writeable = configs.Boolean(default=False)
    _descriptor_config_map = None

    _allowed_search_operators = ["=", "in", "is not null", "is null", "like"]

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
        input_output = self.di.build("input_output", cache=True)
        data = {**data, self.name: input_output.get_client_ip()}
        if self.on_change_pre_save:
            data = self.execute_actions_with_data(self.on_change_pre_save, model, data)
        return data
