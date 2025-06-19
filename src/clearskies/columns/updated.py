from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import clearskies.di
import clearskies.parameters_to_properties
import clearskies.typing
from clearskies import configs
from clearskies.columns.datetime import Datetime

if TYPE_CHECKING:
    from clearskies import Model


class Updated(Datetime):
    """
    The updated column records the time that a record is created or updated.

    Note that this will always populate the column anytime the model is created or updated.
    You don't have to provide the timestamp yourself and you should never expose it as
    a writeable column through an endpoint (in fact, you can't).

    ```python
    import clearskies
    import time


    class MyModel(clearskies.Model):
        backend = clearskies.backends.MemoryBackend()
        id_column_name = "id"

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        created = clearskies.columns.Created()
        updated = clearskies.columns.Updated()


    def test_updated(my_models: MyModel) -> MyModel:
        my_model = my_models.create({"name": "Jane"})
        updated_column_after_create = my_model.updated

        time.sleep(2)

        my_model.save({"name": "Susan"})

        return {
            "updated_column_after_create": updated_column_after_create.isoformat(),
            "updated_column_at_end": my_model.updated.isoformat(),
            "difference_in_seconds": (my_model.updated - updated_column_after_create).total_seconds(),
        }


    cli = clearskies.contexts.Cli(clearskies.endpoints.Callable(test_updated), classes=[MyModel])
    cli()
    ```

    And when invoked:

    ```bash
    $ ./test.py | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "updated_column_after_create": "2025-05-18T19:28:46+00:00",
            "updated_column_at_end": "2025-05-18T19:28:48+00:00",
            "difference_in_seconds": 2.0
        },
        "pagination": {},
        "input_errors": {}
    }
    ```

    Note that the `updated` column was set both when the record was first created and when it was updated,
    so there is a two second difference between them (since we slept for two seconds).

    """

    """
    Created fields are never writeable because they always set the created time automatically.
    """
    is_writeable = configs.Boolean(default=False)
    _descriptor_config_map = None

    now = clearskies.di.inject.Now()

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        in_utc: bool = True,
        date_format: str = "%Y-%m-%d %H:%M:%S",
        backend_default: str = "0000-00-00 00:00:00",
        is_readable: bool = True,
        is_searchable: bool = True,
        is_temporary: bool = False,
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
    ):
        pass

    def pre_save(self, data: dict[str, Any], model: Model) -> dict[str, Any]:
        now = self.now
        if self.timezone_aware:
            now = now.astimezone(self.timezone)
        data = {**data, self.name: now}
        if self.on_change_pre_save:
            data = self.execute_actions_with_data(self.on_change_pre_save, model, data)
        return data
