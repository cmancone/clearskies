from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import clearskies.configs
from clearskies.validator import Validator

if TYPE_CHECKING:
    import clearskies.model


class MaximumLength(Validator):
    maximum_length = clearskies.configs.Integer(required=True)

    def __init__(self, maximum_length: int):
        self.maximum_length = maximum_length
        self.finalize_and_validate_configuration()

    def check(self, model: clearskies.model.Model, column_name: str, data: dict[str, Any]) -> str:
        # we won't check anything for missing values (columns should be required if that is an issue)
        if not data.get(column_name):
            return ""
        if len(data[column_name]) <= self.maximum_length:
            return ""
        return f"'{column_name}' must be at most {self.maximum_length} characters long."
