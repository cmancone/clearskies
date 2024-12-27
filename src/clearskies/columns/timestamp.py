import datetime
from typing import Callable

import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.columns.datetime import Datetime


class Timestamp(Datetime):
    """
    A timestamp column.

    The difference between this and the datetime column is that this stores the datetime
    as a standard unix timestamp - the number of seconds since the unix epoch.

    Also, this ALWAYS assumes the timezone for the timestamp is UTC
    """

    # whether or not to include the milliseconds in the timestamp
    include_microseconds = configs.Boolean(default=False)

    @parameters_to_properties.parameters_to_properties
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

    def from_backend(self, instance, value) -> datetime.datetime | None:
        mult = 1000 if self.milliseconds else 1
        if not value:
            date = None
        elif isinstance(value, str):
            if not value.isdigit():
                raise ValueError(
                    f"Invalid data was found in the backend for model {self.model_class.__name__} and column {self.name}: a string value was found that is not a timestamp.  It was '{value}'"
                )
            date = datetime.fromtimestamp(int(value) / mult, self._timezone)
        elif isinstance(value, int):
            date = datetime.fromtimestamp(value / mult, self._timezone)
        else:
            if not isinstance(value, datetime):
                raise ValueError(
                    f"Invalid data was found in the backend for model {self.model_class.__name__} and column {self.name}: the value was neither an integer, a string, nor a datetime object"
                )
            date = value
        return date.replace(tzinfo=self._timezone) if date else None

    def to_backend(self, data):
        if not self.name in data or isinstance(data[self.name], int) or data[self.name] == None:
            return data

        value = data[self.name]
        if isinstance(value, str):
            if not value.isdigit():
                raise ValueError(
                    f"Invalid data was sent to the backend for model {self.model_class.__name__} and column {self.name}: a string value was found that is not a timestamp. It was '{value}'"
                )
            value = int(value)
        elif isinstance(value, datetime):
            value = value.timestamp()
        else:
            raise ValueError(
                f"Invalid data was sent to the backend for model {self.model_class.__name__} and column {self.name}: the value was neither an integer, a string, nor a datetime object"
            )

        return {**data, self.name: value}

    def __get__(self, instance, parent) -> datetime.datetime | None:
        return super().__get__(instance, parent)

    def __set__(self, instance, value: datetime.datetime) -> None:
        instance._next_data[self.name] = value
