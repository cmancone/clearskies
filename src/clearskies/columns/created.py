import datetime
from typing import Optional

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
    Whether or not to use UTC for the timezone.
    """
    in_utc = configs.Boolean(default=True)

    """
    Whether or not to include microseconds in the time
    """
    include_microseconds = configs.Boolean(default=False)

    """
    Created fields are never writeable because they always set the created time automatically.
    """
    is_writeable = configs.Boolean(default=False)

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        in_utc: bool = True,
        date_format: str | None = None,
        default_date: str | None = None,
        include_microseconds: bool = False,
        validators: Callable | Validator | BindingValidator | list[Callable | Validator | BindingValidator] = [],
        is_readable: bool = True,
        is_temporary: bool = False,
        on_change_pre_save: Callable | Action | BindingAction | list[Callable | Action | BindingAction] = [],
        on_change_post_save: Callable | Action | BindingAction | list[Callable | Action | BindingAction] = [],
        on_change_save_finished: Callable | Action | BindingAction | list[Callable | Action | BindingAction] = [],
    ):
        pass
