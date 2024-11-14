import datetime
from typing import Optional

import clearskies.typing
from clearskies.columns import Datetime
from clearskies import configs, parameters_to_properties

class Created(Datetime):
    """
    The created column records the time that a record is created.

    Note that this will always populate the column when the model is first created.
    You don't have to provide the timestamp yourself and you should never expose it as
    a writeable column through an API (in fact, you can't).

    ```
    import clearskies
    class MyModel(clearskies.model):
        backend = clearskies.backends.MemoryBackend()
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        created = clearskies.columns.Created()

    def my_application(my_models):
        my_model = my_models.create({"name": "Example"})

        # prints a datetime object with the current time in UTC
        print(my_model.created)

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
        date_format: str = "%Y-%m-%d %H:%M:%S",
        in_utc: bool = True,
        backend_default: str = "0000-00-00 00:00:00",
        is_readable: bool = True,
        is_temporary: bool = False,
        on_change_pre_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_post_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_save_finished: clearskies.typing.actions | list[clearskies.typing.actions] = [],
    ):
        pass
