from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Callable, Self, overload

import dateparser  # type: ignore

import clearskies.parameters_to_properties
import clearskies.typing
from clearskies import configs
from clearskies.autodoc.schema import Datetime as AutoDocDatetime
from clearskies.autodoc.schema import Schema as AutoDocSchema
from clearskies.column import Column
from clearskies.query import Condition

if TYPE_CHECKING:
    from clearskies import Model


class Datetime(Column):
    """
    Stores date+time data in a column.

    When processing user input, this value is passed through `dateparser.parse()` to decide if it is a proper date string.
    This makes for relatively flexible input validation.  Example:

    ```python
    import clearskies


    class MyModel(clearskies.Model):
        backend = clearskies.backends.MemoryBackend()
        id_column_name = "id"

        id = clearskies.columns.Uuid()
        name = clearskies.columns.String()
        my_datetime = clearskies.columns.Datetime()


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Create(
            MyModel,
            writeable_column_names=["name", "my_datetime"],
            readable_column_names=["id", "name", "my_datetime"],
        ),
        classes=[MyModel],
    )
    wsgi()
    ```

    And when invoked:

    ```bash
    $ curl 'http://localhost:8080' -d '{"name":"Bob", "my_datetime":"2025-05-13 12:35:45+00:00"}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "68095d0d-c909-4ab3-8c15-bd2667b7b074",
            "name": "Bob",
            "my_datetime": "2025-05-13T12:35:45+00:00"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080' -d '{"name":"Bob", "my_datetime":"May 13th 2025 2:35:45UTC"}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "9fea6933-86ac-4dd1-b9e0-a9fa50608410",
            "name": "Bob",
            "my_datetime": "2025-05-13T12:35:45+00:00"
        },
        "pagination": {},
        "input_errors": {}
    }

    $ curl 'http://localhost:8080' -d '{"name":"Bob", "my_datetime":"not a date"}' | jq
    {
        "status": "input_errors",
        "error": "",
        "data": [],
        "pagination": {},
        "input_errors": {
            "my_datetime": "given value did not appear to be a valid date"
        }
    }
    ```
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
    default = configs.Datetime()  # type: ignore

    """
    Sets a default date that the backend is going to provide.

    Some backends, depending on configuration, may provide a default value for the column
    instead of null.  By setting this equal to that default value, clearskies can detect
    when a given value is actually a non-value.
    """
    backend_default = configs.String(default="0000-00-00 00:00:00")

    setable = configs.DatetimeOrCallable(default=None)  # type: ignore
    _allowed_search_operators = ["<=>", "!=", "<=", ">=", ">", "<", "=", "in", "is not null", "is null"]
    auto_doc_class: type[AutoDocSchema] = AutoDocDatetime
    _descriptor_config_map = None

    @clearskies.parameters_to_properties.parameters_to_properties
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

    def from_backend(self, value) -> datetime.datetime | None:
        if not value or value == self.backend_default:
            return None
        if isinstance(value, str):
            value = dateparser.parse(value)
        if not isinstance(value, datetime.datetime):
            raise TypeError(
                f"I was expecting to get a datetime from the backend but I didn't get anything recognizable.  I have a value of type '{value.__class__.__name__}'.  I need either a datetime object or a datetime serialized as a string."
            )
        if self.timezone_aware:
            if not value.tzinfo:
                value = value.replace(tzinfo=self.timezone)
            elif value.tzinfo != self.timezone:
                value = value.astimezone(self.timezone)
        else:
            value = value.replace(tzinfo=None)

        return value

    def to_backend(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.name not in data or isinstance(data[self.name], str) or data[self.name] is None:
            return data

        value = data[self.name]
        if not isinstance(data[self.name], datetime.datetime):
            raise TypeError(
                f"I was expecting a stringified-date or a datetime object to send to the backend, but instead I found a value of {value.__class__.__name__}"
            )

        return {
            **data,
            self.name: value.strftime(self.date_format),
        }

    def to_json(self, model: clearskies.model.Model) -> dict[str, Any]:
        """Grabs the column out of the model and converts it into a representation that can be turned into JSON."""
        value = self.__get__(model, model.__class__)
        if value and (isinstance(value, datetime.datetime) or isinstance(value, datetime.date)):
            value = value.isoformat()  # type: ignore

        return {self.name: value}

    @overload
    def __get__(self, instance: None, cls: type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: type[Model]) -> datetime.datetime:
        pass

    def __get__(self, instance, cls):
        return super().__get__(instance, cls)

    def __set__(self, instance, value: datetime.datetime) -> None:
        instance._next_data[self.name] = value

    def equals(self, value: str | datetime.datetime) -> Condition:
        return super().equals(value)

    def spaceship(self, value: str | datetime.datetime) -> Condition:
        return super().spaceship(value)

    def not_equals(self, value: str | datetime.datetime) -> Condition:
        return super().not_equals(value)

    def less_than_equals(self, value: str | datetime.datetime) -> Condition:
        return super().less_than_equals(value)

    def greater_than_equals(self, value: str | datetime.datetime) -> Condition:
        return super().greater_than_equals(value)

    def less_than(self, value: str | datetime.datetime) -> Condition:
        return super().less_than(value)

    def greater_than(self, value: str | datetime.datetime) -> Condition:
        return super().greater_than(value)

    def is_in(self, values: list[str | datetime.datetime]) -> Condition:
        return super().is_in(values)

    def input_error_for_value(self, value, operator=None):
        value = dateparser.parse(value)
        if not value:
            return "given value did not appear to be a valid date"
        if not value.tzinfo and self.timezone_aware:
            return "date is missing timezone information"
        return ""

    def values_match(self, value_1, value_2):
        """Compare two values to see if they are the same."""
        # in this function we deal with data directly out of the backend, so our date is likely
        # to be string-ified and we want to look for default (e.g. null) values in string form.
        if type(value_1) == str and ("0000-00-00" in value_1 or value_1 == self.backend_default):
            value_1 = None
        if type(value_2) == str and ("0000-00-00" in value_2 or value_2 == self.backend_default):
            value_2 = None
        number_values = 0
        if value_1:
            number_values += 1
        if value_2:
            number_values += 1
        if number_values == 0:
            return True
        if number_values == 1:
            return False

        if type(value_1) == str:
            value_1 = dateparser.parse(value_1)
        if type(value_2) == str:
            value_2 = dateparser.parse(value_2)

        # we need to make sure we're comparing in the same timezones.  For our purposes, a difference in timezone
        # is fine as long as they represent the same time (e.g. 16:00EST == 20:00UTC).  For python, same time in different
        # timezones is treated as different datetime objects.
        if value_1.tzinfo is not None and value_2.tzinfo is not None:
            value_1 = value_1.astimezone(value_2.tzinfo)

        # two times can be the same but if one is datetime-aware and one is not, python will treat them as not equal.
        # we want to treat such times as being the same.  Therefore, check for equality but ignore the timezone.
        for to_check in ["year", "month", "day", "hour", "minute", "second", "microsecond"]:
            if getattr(value_1, to_check) != getattr(value_2, to_check):
                return False

        # and since we already converted the timezones to match (or one has a timezone and one doesn't), we're good to go.
        # if we passed the above loop then the times are the same.
        return True
