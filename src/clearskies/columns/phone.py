import re
from typing import Any, Callable

import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.columns.string import String


class Phone(String):
    """
    A string column that stores a phone number.

    The main difference between this and a plain string column is that this will validate that the string contains
    a phone number (containing only digits, dashes, spaces, plus sign, and parenthesis) of the appropriate length.
    When persisting the value to the backend, this column removes all non-digit characters.

    If you also set the usa_only flag to true then it will also validate that it is a valid US number containing
    9 digits and, optionally, a leading `1`.  Example:

    ```python
    import clearskies


    class User(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        phone = clearskies.columns.Phone(usa_only=True)


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Create(
            User,
            writeable_column_names=["name", "phone"],
            readable_column_names=["id", "name", "phone"],
        ),
    )
    wsgi()
    ```

    Which you can invoke:

    ```bash
    $ curl http://localhost:8080 -d '{"name":"John Doe", "phone": "+1 (555) 451-1234"}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "e2b4bdad-b70f-4d44-a94c-0e265868b4d2",
            "name": "John Doe",
            "phone": "15554511234"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl http://localhost:8080 -d '{"name":"John Doe", "phone": "555 451-1234"}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "aea34022-4b75-4eed-ac92-65fa4f4511ae",
            "name": "John Doe",
            "phone": "5554511234"
        },
        "pagination": {},
        "input_errors": {}
    }


    $ curl http://localhost:8080 -d '{"name":"John Doe", "phone": "555 451-12341"}' | jq
    {
        "status": "input_errors",
        "error": "",
        "data": [],
        "pagination": {},
        "input_errors": {
            "phone": "Invalid phone number"
        }
    }

    $ curl http://localhost:8080 -d '{"name":"John Doe", "phone": "1-2-3-4 asdf"}' | jq
    {
        "status": "input_errors",
        "error": "",
        "data": [],
        "pagination": {},
        "input_errors": {
            "phone": "Invalid phone number"
        }
    }
    ```
    """

    """ Whether or not to allow non-USA numbers. """
    usa_only = configs.Boolean(default=True)
    _descriptor_config_map = None

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        usa_only: bool = True,
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

    def input_error_for_value(self, value: str, operator: str | None = None) -> str:
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
            if value[0] != "1" and len(value) != 10:
                return "Invalid phone number"

        return ""
