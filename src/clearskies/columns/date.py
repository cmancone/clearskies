from __future__ import annotations
import datetime
from typing import Any, Callable, overload, Self, TYPE_CHECKING, Type

import dateparser # type: ignore

import clearskies.typing
import clearskies.parameters_to_properties
from clearskies import configs
from clearskies.columns.datetime import Datetime
from clearskies.autodoc.schema import Schema as AutoDocSchema
from clearskies.autodoc.schema import Datetime as AutoDocDatetime
from clearskies.query import Condition

if TYPE_CHECKING:
    from clearskies import Model

class Date(Datetime):
    """
    Stores date data in a column.
    """

    """
    The format string to use when sending to the backend (default: %Y-%m-%d)
    """
    date_format = configs.String(default="%Y-%m-%d")

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
    backend_default = configs.String(default="0000-00-00")

    """
    A value to set for this column during a save operation.

    Unlike the default value, a setable value is always set during a save.
    """
    setable = configs.DatetimeOrCallable(default=None)  # type: ignore

    _allowed_search_operators = ["<=>", "!=", "<=", ">=", ">", "<", "=", "in", "is not null", "is null"]

    """
    The class to use when documenting this column
    """
    auto_doc_class: Type[AutoDocSchema] = AutoDocDatetime
    _descriptor_config_map = None

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        date_format: str = "%Y-%m-%d",
        backend_default: str = "0000-00-00",
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

    def from_backend(self, value) -> datetime.date | None:
        if not value or value == self.backend_default:
            return None
        if isinstance(value, str):
            value = dateparser.parse(value)
        if not isinstance(value, datetime.datetime):
            raise TypeError(f"I was expecting to get a datetime from the backend but I didn't get anything recognizable.  I have a value of type '{value.__class__.__name__}'.  I need either a datetime object or a datetime serialized as a string.")

        return datetime.date(value.year, value.month, value.day)

    def to_backend(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.name not in data or isinstance(data[self.name], str) or data[self.name] is None:
            return data

        value = data[self.name]
        if not isinstance(data[self.name], datetime.datetime) and not isinstance(data[self.name], datetime.date):
            raise TypeError(f"I was expecting a stringified-date or a datetime object to send to the backend, but instead I found a value of {value.__class__.__name__}")

        return {
            **data,
            self.name: value.strftime(self.date_format),
        }

    @overload
    def __get__(self, instance: None, cls: Type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: Type[Model]) -> datetime.date:
        pass

    def __get__(self, instance, cls):
        return super().__get__(instance, cls)

    def __set__(self, instance, value: datetime.datetime | datetime.date) -> None:
        instance._next_data[self.name] = value

    def equals(self, value: str | datetime.datetime | datetime.date) -> Condition:
        return super().equals(value)

    def spaceship(self, value: str | datetime.datetime | datetime.date) -> Condition:
        return super().spaceship(value)

    def not_equals(self, value: str | datetime.datetime | datetime.date) -> Condition:
        return super().not_equals(value)

    def less_than_equals(self, value: str | datetime.datetime | datetime.date) -> Condition:
        return super().less_than_equals(value)

    def greater_than_equals(self, value: str | datetime.datetime | datetime.date) -> Condition:
        return super().greater_than_equals(value)

    def less_than(self, value: str | datetime.datetime | datetime.date) -> Condition:
        return super().less_than(value)

    def greater_than(self, value: str | datetime.datetime | datetime.date) -> Condition:
        return super().greater_than(value)

    def is_in(self, values: list[str | datetime.datetime | datetime.date]) -> Condition:
        return super().is_in(values)

    def input_error_for_value(self, value, operator=None):
        value = dateparser.parse(value)
        if not value:
            return "given value did not appear to be a valid date"
        return ""

    def values_match(self, value_1, value_2):
        """
        Compares two values to see if they are the same
        """
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
            value_1 = datetime.date(value_1.year, value_1.month, value_1.day)
        if type(value_2) == str:
            value_2 = dateparser.parse(value_2)
            value_2 = datetime.date(value_2.year, value_2.month, value_2.day)

        # two times can be the same but if one is datetime-aware and one is not, python will treat them as not equal.
        # we want to treat such times as being the same.  Therefore, check for equality but ignore the timezone.
        for to_check in ["year", "month", "day"]:
            if getattr(value_1, to_check) != getattr(value_2, to_check):
                return False

        # and since we already converted the timezones to match (or one has a timezone and one doesn't), we're good to go.
        # if we passed the above loop then the times are the same.
        return True
