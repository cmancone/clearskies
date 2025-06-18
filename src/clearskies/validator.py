from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from clearskies import configurable

if TYPE_CHECKING:
    import clearskies.column
    import clearskies.model


class Validator(ABC, configurable.Configurable):
    is_unique = False
    is_required = False

    def __call__(self, model: clearskies.model.Model, column_name: str, data: dict[str, Any]) -> str:
        return self.check(model, column_name, data)

    @abstractmethod
    def check(self, model: clearskies.model.Model, column_name: str, data: dict[str, Any]) -> str:
        pass

    def additional_write_columns(self, is_create=False) -> dict[str, clearskies.column.Column]:
        return {}
