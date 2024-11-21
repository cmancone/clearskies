from abc import ABC, abstractmethod
from typing import Dict, Any


class Validator(ABC):
    is_unique = False
    is_required = False

    @property
    def column_name(self) -> str:
        if self._column_name is None:
            raise ValueError("Attempt to get column name on requirement before setting it")
        return self._column_name

    @column_name.setter
    def column_name(self, column_name: str):
        self._column_name = column_name

    def configure(self):
        pass

    @abstractmethod
    def check(self, data: Dict[str, Any]):
        pass

    def additional_write_columns(self, is_create=False) -> Dict[str, Any]:
        return {}
