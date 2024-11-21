import clearskies.typing
from clearskies.column import Column
from clearskies import configs, parameters_to_properties


class Uuid(Column):
    """
    Populates the column with a UUID upon record creation.

    This column really just has a very specific purpose: ids!

    When used, it will automatically populate the column with a random UUID upon record creation.
    It is not a writeable column, which means that you cannot expose it for write operations via the API.

    ```
    import clearskies

    class MyModel(clearskies.Model):
        id_column_name = "id"
        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()

    def my_application(my_models):
        model = my_models.create({"name": "hey"})
        print(len(model.id))
        # prints 36
    ```
    """

    is_writeable = configs.Boolean(default=False)

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        is_readable: bool = True,
        is_temporary: bool = False,
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
    ):
        pass
