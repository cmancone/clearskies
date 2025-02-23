from typing import Any, Callable
import re

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
    _descriptor_config_map = None

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
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

    def to_backend(self, data: dict[str, Any]) -> dict[str, Any]:
        if not data.get(self.name):
            return data

        # phone numbers are stored as only digits.
        return {**data, **{self.name: re.sub(r"\D", "", data[self.name])}}

    def input_error_for_value(self, value: str, operator: str | None=None) -> str:
        if type(value) != str:
            return f"Value must be a string for {self.name}"

        # we'll allow spaces, dashes, parenthesis, dashes, and plus signs.
        # if there is anything else then it's not a valid phone number.
        # However, we don't do more detailed validation, because I'm too lazy to
        # figure out what is and is not a valid phone number, especially when
        # you get to the world of international numbers.
        if re.search(r"[^\d \-()+]", value):
            return "Invalid phone number"

        # for some final validation (especially US numbers) work only with the digits.
        value = re.sub(r"\D", "", value)

        if len(value) > 15:
            return "Invalid phone number"

        # we can't be too short unless we're doing a fuzzy search
        if len(value) < 10 and operator and operator.lower() != "like":
            return "Invalid phone number"

        if self.usa_only:
            if len(value) > 11:
                return "Invalid phone number"
            if value[0] == "1" and len(value) != 11:
                return "Invalid phone number"

        return ""
