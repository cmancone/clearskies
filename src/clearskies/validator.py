from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING
from clearskies import configurable

if TYPE_CHECKING:
    import clearskies.model
    import clearskies.column

class Validator(ABC, configurable.Configurable):
    is_unique = False
    is_required = False

    @abstractmethod
    def check(self, model: clearskies.model.Model, column_name: str, data: dict[str, Any]) -> str:
        pass

    def additional_write_columns(self, is_create=False) -> dict[str, clearskies.column.Column]:
        return {}
