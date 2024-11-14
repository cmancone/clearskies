import datetime
from typing import Callable

import clearskies.typing
from clearskies.columns.datetime import Datetime
from clearskies import configs, parameters_to_properties


class Updated(Datetime):
    """
    The updated column records the time that a record is created or updated.

    Note that this will always populate the column anytime the model is created or updated.
    You don't have to provide the timestamp yourself and you should never expose it as
    a writeable column through an API (in fact, you can't).

    ```
    import clearskies
    import time

    class MyModel(clearskies.model):
        backend = clearskies.backends.MemoryBackend()
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        updated = clearskies.columns.Updated()

    def my_application(my_models):
        my_model = my_models.create({"name": "Example"})

        # prints a datetime object with the current time in UTC
        print(my_model.updated)

        time.sleep(1)
        my_model.save({"name": "Another"})

        # prints a datetime object with the current time in UTC, roughly one second later than before
        print(my_model.updated)

    cli = clearskies.contexts.cli(my_model, binding_classes=[MyModel])
    cli()
    ```
    """

    """
    Created fields are never writeable because they always set the created time automatically.
    """
    is_writeable = configs.Boolean(default=False)

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        in_utc: bool = True,
        date_format: str = "%Y-%m-%d %H:%M:%S",
        backend_default: str = "0000-00-00 00:00:00",
        is_readable: bool = True,
        is_temporary: bool = False,
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
    ):
        pass
