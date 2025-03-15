from __future__ import annotations
from typing import Any, TYPE_CHECKING
import datetime

from clearskies.validator import Validator
import clearskies.configs

if TYPE_CHECKING:
    import clearskies.model


class MinimumLength(Validator):
    minimum_length = clearskies.configs.Integer(required=True)

    def __init__(self, minimum_length: int):
        self.minimum_length = minimum_length
        self.finalize_and_validate_configuration()

    def check(self, model: clearskies.model.Model, column_name: str, data: dict[str, Any]) -> str:
        # we won't check anything for missing values (columns should be required if that is an issue)
        if not data.get(column_name):
            return ""
        if len(data[column_name]) >= self.minimum_length:
            return ""
        return f"'{column_name}' must be at least {self.minimum_length} characters long."
