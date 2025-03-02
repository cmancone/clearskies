from __future__ import annotations
from typing import Any, TYPE_CHECKING
import datetime

from clearskies.validator import Validator
import clearskies.configs
from clearskies import parameters_to_properties

if TYPE_CHECKING:
    import clearskies.model


class MaximumLength(Validator):
    maximum_length = clearskies.configs.Integer(required=True)

    @parameters_to_properties
    def __init__(self, maximum_length: int):
        self.finalize_and_validate_configuration()

    def check(self, model: clearskies.model.Model, column_name: str, data: dict[str, Any]) -> str:
        # we won't check anything for missing values (columns should be required if that is an issue)
        if not data.get(column_name):
            return ""
        if len(data[column_name]) <= self.maximum_length:
            return ""
        return f"'{column_name}' must be at most {self.maximum_length} characters long."
