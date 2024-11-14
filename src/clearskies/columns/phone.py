from typing import Callable

import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.columns.string import String


class Phone(String):
    """
    A column that stores a phone number.

    This will validate the number and, in the backend, convert it to digits only.

    If you also set the usa_only flag to true then it will also validate that it is
    a valid US number - 9 digits and, optionally, a leading `1`.
    """

    """ Whether or not to allow non-USA numbers. """
    usa_only = configs.Boolean(default=True)

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        default: str | None = None,
        setable: str | Callable[..., str] | None = None,
        is_readable: bool = True,
        is_writeable: bool = True,
        is_temporary: bool = False,
        validators: clearskies.typing.validator | list[clearskies.typing.validator] = [],
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
        created_by_source_type: str = "",
        created_by_source_key: str = "",
    ):
        pass
