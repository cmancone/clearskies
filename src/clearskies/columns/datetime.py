import datetime
from typing import Callable

import dateparser

import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.column import Column


class Datetime(Column):
    """
    Stores date+time data in a column.
    """

    """
    Whether or not to make datetime objects timezone-aware
    """
    timezone_aware = configs.Boolean(default=True)

    """
    The timezone to use for the datetime object (if it is timezone aware)
    """
    timezone = configs.Timezone(default=datetime.timezone.utc)

    """
    The format string to use when sending to the backend (default: %Y-%m-%d %H:%M:%S)
    """
    date_format = configs.String(default="%Y-%m-%d %H:%M:%S")

    """
    A default value to set for this column.

    The default is only used when creating a record for the first time, and only if
    a value for this column has not been set.
    """
    default = configs.Datetime()

    """
    Sets a default date that the backend is going to provide.

    Some backends, depending on configuration, may provide a default value for the column
    instead of null.  By setting this equal to that default value, clearskies can detect
    when a given value is actually a non-value.
    """
    backend_default = configs.String(default="0000-00-00 00:00:00")

    """
    A value to set for this column during a save operation.

    Unlike the default value, a setable value is always set during a save.
    """
    setable = configs.DatetimeOrCallable(default=None)

    @parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        date_format: str = "%Y-%m-%d %H:%M:%S",
        backend_default: str = "0000-00-00 00:00:00",
        timezone_aware: bool = True,
        timezone: datetime.timezone = datetime.timezone.utc,
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
        if not value or value == self.backend_default:
            return None
        if isinstance(value, str):
            value = dateparser.parse(value)
        if not isinstance(value, datetime.datetime):
            raise TypeError(f"I was expecting to get a datetime from the backend but I didn't get anything recognizable.  I have a value of type '{value.__class__.__name__}'.  I need either a datetime object or a datetime serialized as a string.")
        if self.timezone_aware:
            if not value.tzinfo:
                value = value.replace(tzinfo=self.timezone)
            elif value.tzinfo != self.timezone:
                value = value.astimezone(self.timezone)
        else:
            value.tzinfo = None

        return value

    def to_backend(self, data):
        if self.name not in data or isinstance(data[self.name], str) or data[self.name] is None:
            return data

        value = data[self.name]
        if not isinstance(data[self.name], datetime.datetime):
            raise TypeError(f"I was expecting a stringified-date or a datetime object to send to the backend, but instead I found a value of {value.__class__.__name__}")

        return {
            **data,
            self.name: value.strftime(self.date_format),
        }

    def __get__(self, instance, parent) -> datetime.datetime | None:
        return super().__get__(instance, parent)

    def __set__(self, instance, value: datetime.datetime) -> None:
        instance._next_data[self.name] = value
