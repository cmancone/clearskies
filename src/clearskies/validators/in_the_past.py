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


class InThePast(Validator, clearskies.di.InjectableProperties):
    utcnow = clearskies.di.inject.Utcnow()

    def check(self, model: clearskies.model.Model, column_name: str, data: dict[str, Any]) -> str:
        if not data.get(column_name):
            return ""

        as_date = dateparser.parse(data[column_name]) if isinstance(data[column_name], str) else data[column_name]
        if not as_date:
            return f"'{column_name}' was not a valid date"
        if as_date.tzinfo == None:
            as_date = as_date.replace(tzinfo=datetime.timezone.utc)
        if as_date >= self.utcnow:
            return f"'{column_name}' must be in the past"
        return ""
