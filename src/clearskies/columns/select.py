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
        is_searchable: bool = True,
        is_temporary: bool = False,
        validators: clearskies.typing.validator | list[clearskies.typing.validator] = [],
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
        created_by_source_type: str = "",
        created_by_source_key: str = "",
        created_by_source_strict: bool = True,
    ):
        pass

    def input_error_for_value(self, value: str, operator: str | None=None) -> str:
        return f"Invalid value for {self.name}" if value not in self.allowed_values else ""
