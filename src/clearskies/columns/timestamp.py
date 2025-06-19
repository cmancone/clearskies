from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Callable, Self, Type, overload

import clearskies.parameters_to_properties
import clearskies.typing
from clearskies import configs
from clearskies.columns.datetime import Datetime

if TYPE_CHECKING:
    from clearskies import Model


class Timestamp(Datetime):
    """
    A timestamp column.

    The difference between this and the datetime column is that this stores the datetime
    as a standard unix timestamp - the number of seconds since the unix epoch.

    Also, this **always** assumes the timezone for the timestamp is UTC

    ```python
    import datetime
    import clearskies


    class Pet(clearskies.Model):
        id_column_name = "id"
        backend = clearskies.backends.MemoryBackend()

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        last_fed = clearskies.columns.Timestamp()


    def demo_timestamp(utcnow: datetime.datetime, pets: Pet) -> dict[str, str | int]:
        pet = pets.create({
            "name": "Spot",
            "last_fed": utcnow,
        })
        return {
            "last_fed": pet.last_fed.isoformat(),
            "raw_data": pet.get_raw_data()["last_fed"],
        }


    cli = clearskies.contexts.Cli(
        clearskies.endpoints.Callable(
            demo_timestamp,
        ),
        classes=[Pet],
    )
    cli()
    ```

    And when invoked it returns:

    ```json
    {
        "status": "success",
        "error": "",
        "data": {"last_fed": "2025-05-18T19:14:56+00:00", "raw_data": 1747595696},
        "pagination": {},
        "input_errors": {},
    }
    ```

    Note that if you pull the column from the model in the usual way (e.g. `pet.last_fed` you get a timestamp,
    but if you check the raw data straight out of the backend (e.g. `pet.get_raw_data()["last_fed"]`) it's an
    integer.
    """

    # whether or not to include the microseconds in the timestamp
    include_microseconds = configs.Boolean(default=False)
    _descriptor_config_map = None

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        include_microseconds: bool = False,
        default: datetime.datetime | None = None,
        setable: datetime.datetime | Callable[..., datetime.datetime] | None = None,
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

    def from_backend(self, value) -> datetime.datetime | None:
        mult = 1000 if self.include_microseconds else 1
        if not value:
            date = None
        elif isinstance(value, str):
            if not value.isdigit():
                raise ValueError(
                    f"Invalid data was found in the backend for model {self.model_class.__name__} and column {self.name}: a string value was found that is not a timestamp.  It was '{value}'"
                )
            date = datetime.datetime.fromtimestamp(int(value) / mult, datetime.timezone.utc)
        elif isinstance(value, int) or isinstance(value, float):
            date = datetime.datetime.fromtimestamp(value / mult, datetime.timezone.utc)
        else:
            if not isinstance(value, datetime.datetime):
                raise ValueError(
                    f"Invalid data was found in the backend for model {self.model_class.__name__} and column {self.name}: the value was neither an integer, float, string, or datetime object"
                )
            date = value
        return date.replace(tzinfo=datetime.timezone.utc) if date else None

    def to_backend(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self.name in data or isinstance(data[self.name], int) or data[self.name] == None:
            return data

        value = data[self.name]
        if isinstance(value, str):
            if not value.isdigit():
                raise ValueError(
                    f"Invalid data was sent to the backend for model {self.model_class.__name__} and column {self.name}: a string value was found that is not a timestamp. It was '{value}'"
                )
            value = int(value)
        elif isinstance(value, datetime.datetime):
            value = value.timestamp()
        else:
            raise ValueError(
                f"Invalid data was sent to the backend for model {self.model_class.__name__} and column {self.name}: the value was neither an integer, a string, nor a datetime object"
            )

        return {**data, self.name: int(value)}

    @overload
    def __get__(self, instance: None, cls: type) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: type) -> datetime.datetime:
        pass

    def __get__(self, instance, cls):
        return super().__get__(instance, cls)

    def __set__(self, instance, value: datetime.datetime) -> None:
        instance._next_data[self.name] = value

    def input_error_for_value(self, value: str, operator: str | None = None) -> str:
        if not isinstance(value, int):
            return f"'{self.name}' must be an integer"
        return ""

    def values_match(self, value_1, value_2):
        """Compare two values to see if they are the same."""
        return value_1 == value_2
