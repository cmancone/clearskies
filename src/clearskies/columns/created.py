from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import clearskies.di
import clearskies.typing
from clearskies import configs, parameters_to_properties  # type: ignore
from clearskies.columns.datetime import Datetime

if TYPE_CHECKING:
    from clearskies import Model


class Created(Datetime):
    """
    The created column records the time that a record is created.

    This will always populate the column when the model is first created.  If you attempt to set a value
    to this column on create then it will be overwritten.

    ```python
    import clearskies


    class MyModel(clearskies.Model):
        backend = clearskies.backends.MemoryBackend()
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        created = clearskies.columns.Created()


    cli = clearskies.contexts.Cli(
        clearskies.endpoints.Callable(
            lambda my_models: my_models.create({"name": "An Example"}),
            model_class=MyModel,
            readable_column_names=["id", "name", "created"],
        ),
        classes=[MyModel],
    )
    cli()
    ```

    And if you execute this you'll see that the `created` column was automatically populated:

    ```json
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "c54d74ac-5282-439e-af4f-23efb9ba96d4",
            "name": "An Example",
            "created": "2025-05-09T19:58:43+00:00",
        },
        "pagination": {},
        "input_errors": {},
    }
    ```
    """

    """
    Created fields are never writeable because they always set the created time automatically.
    """
    is_writeable = configs.Boolean(default=False)
    _descriptor_config_map = None

    now = clearskies.di.inject.Now()

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        date_format: str = "%Y-%m-%d %H:%M:%S",
        in_utc: bool = True,
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
        if model:
            return data
        now = self.now
        if self.timezone_aware:
            now = now.astimezone(self.timezone)
        data = {**data, self.name: now}
        if self.on_change_pre_save:
            data = self.execute_actions_with_data(self.on_change_pre_save, model, data)
        return data
