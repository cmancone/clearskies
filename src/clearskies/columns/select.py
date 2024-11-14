from typing import Callable

import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.columns.string import String


class Select(String):
    """
    A string column but, when writeable via an API, only specific values are allowed.
    """

    """ The allowed values. """
    allowed_values = configs.StringList(required=True)

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        allowed_values: list[str],
        default: str | None = None,
        setable: str | Callable[..., str] | None = None,
        is_readable: bool = True,
        is_writeable: bool = True,
        is_temporary: bool = False,
        validators: clearskies.typing.validators | list[clearskies.typing.validators] = [],
        on_change_pre_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_post_save: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        on_change_save_finished: clearskies.typing.actions | list[clearskies.typing.actions] = [],
        created_by_source_type: str = "",
        created_by_source_key: str = "",
    ):
        pass
