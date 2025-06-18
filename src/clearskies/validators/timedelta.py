from __future__ import annotations

import datetime
from collections import OrderedDict
from typing import TYPE_CHECKING, Any

import dateparser

import clearskies.configs
import clearskies.di
import clearskies.parameters_to_properties
from clearskies.validator import Validator

if TYPE_CHECKING:
    import clearskies.model


class Timedelta(Validator, clearskies.di.InjectableProperties):
    timedelta = clearskies.configs.Timedelta(default=None)

    utcnow = clearskies.di.inject.Utcnow()

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(self, timedelta: datetime.timedelta):
        self.finalize_and_validate_configuration()

    def delta_human_friendly(self):
        remainder = int(self.timedelta.total_seconds())
        parts = []
        conversion = OrderedDict(
            [
                ("year", 31536000),
                ("day", 86400),
                ("hour", 3600),
                ("minute", 60),
                ("second", 1),
            ]
        )
        for name, num_seconds in conversion.items():
            if num_seconds > remainder:
                continue
            amount = int(remainder / num_seconds)
            remainder -= amount * num_seconds
            parts.append(f"{amount} {name}" + ("s" if amount != 1 else ""))
        return ", ".join(parts)

    def check(self, model: clearskies.model.Model, column_name: str, data: dict[str, Any]) -> str:
        if not data.get(column_name):
            return ""

        as_date = dateparser.parse(data[column_name]) if isinstance(data[column_name], str) else data[column_name]
        if not as_date:
            return f"'{column_name}' was not a valid date"
        if as_date.tzinfo == None:
            as_date = as_date.replace(tzinfo=datetime.timezone.utc)
        return self.check_timedelta(as_date, column_name)

    def check_timedelta(self, as_date: datetime.datetime, column_name: str) -> str:
        return ""
