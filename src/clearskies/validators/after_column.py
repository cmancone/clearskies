from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import dateparser

import clearskies.configs
import clearskies.parameters_to_properties
from clearskies.validator import Validator

if TYPE_CHECKING:
    import clearskies.model


class AfterColumn(Validator):
    """The name of the other date column for comparison."""

    other_column_name = clearskies.configs.String(default="", required=True)

    """
    If true, then this column is allowed to be eqaul to the other column.
    """
    allow_equal = clearskies.configs.Boolean(default=False)

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(self, other_column_name: str, allow_equal: bool = False):
        self.other_column_name = other_column_name
        self.allow_equal = allow_equal
        self.finalize_and_validate_configuration()

    def check(self, model: clearskies.model.Model, column_name: str, data: dict[str, Any]) -> str:
        # we won't check anything for missing values (columns should be required if that is an issue)
        if not data.get(column_name):
            return ""
        my_value = data[column_name]
        other_value = data.get(self.other_column_name, getattr(model, self.other_column_name))
        # again, no checks for non-values
        if not other_value:
            return ""

        my_value = dateparser.parse(my_value) if isinstance(my_value, str) else my_value
        if not my_value:
            return f"'{column_name}' was not a valid date."

        if type(other_value) != str and type(other_value) != datetime.datetime:
            return f"'{self.other_column_name}' was not a valid date."
        other_value = dateparser.parse(other_value) if isinstance(other_value, str) else other_value
        if not other_value:
            return f"'{self.other_column_name}' was not a valid date."

        return self.date_comparison(my_value, other_value, column_name)

    def date_comparison(
        self, incoming_date: datetime.datetime, comparison_date: datetime.datetime, column_name: str
    ) -> str:
        if incoming_date == comparison_date:
            return "" if self.allow_equal else f"'{column_name}' must be after '{self.other_column_name}'"

        if incoming_date < comparison_date:
            return f"'{column_name}' must be after '{self.other_column_name}'"
        return ""
