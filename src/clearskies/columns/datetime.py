import datetime
from typing import Callable

import clearskies.typing
from clearskies import configs, parameters_to_properties
from clearskies.columns.column import Column


class Datetime(Column):
    """
    Stores date+time data in a column.
    """

    """
    Whether or not to use UTC for the timezone.
    """
    in_utc = configs.Boolean(default=True)

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
        in_utc: bool = True,
        default: datetime.datetime | None = None,
        setable: datetime.datetime | Callable[..., datetime.datetime] | None = None,
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

    def __get__(self, instance, parent) -> datetime.datetime:
        if not instance:
            return self  # type: ignore

        return instance._data[self._my_name(instance)]

    def __set__(self, instance, value: datetime.datetime) -> None:
        instance._next_data[self._my_name(instance)] = value
