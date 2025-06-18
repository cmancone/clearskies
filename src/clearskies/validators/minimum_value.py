from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import clearskies.configs
from clearskies.validator import Validator

if TYPE_CHECKING:
    import clearskies.model


class MinimumValue(Validator):
    minimum_value = clearskies.configs.Integer(required=True)

    def __init__(self, minimum_value: int):
        self.minimum_value = minimum_value
        self.finalize_and_validate_configuration()

    def check(self, model: clearskies.model.Model, column_name: str, data: dict[str, Any]) -> str:
        if column_name not in data:
            return ""
        try:
            value = float(data[column_name])
        except ValueError:
            return f"{column_name} must be an integer or float"
        if float(value) >= self.minimum_value:
            return ""
        return f"'{column_name}' must be at least {self.minimum_value}."
