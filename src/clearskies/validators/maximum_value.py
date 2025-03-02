from __future__ import annotations
from typing import Any, TYPE_CHECKING
import datetime

from clearskies.validator import Validator
import clearskies.configs
from clearskies import parameters_to_properties

if TYPE_CHECKING:
    import clearskies.model


class MaximumValue(Validator):
    maximum_value = clearskies.configs.Integer(required=True)

    @parameters_to_properties
    def __init__(self, maximum_value: int):
        self.finalize_and_validate_configuration()

    def check(self, model: clearskies.model.Model, column_name: str, data: dict[str, Any]) -> str:
        if column_name not in data:
            return ""
        try:
            value = float(data[column_name])
        except ValueError:
            return f"{column_name} must be an integer or float"
        if float(value) <= self.maximum_value:
            return ""
        return f"'{column_name}' must be at most {self.maximum_value}."
