from abc import ABC, abstractmethod


class Requirement(ABC):
    _column_name = None

    @property
    def column_name(self):
        if self._column_name is None:
            raise ValueError("Attempt to get column name on requirement before setting it")
        return self._column_name

    @column_name.setter
    def column_name(self, column_name):
        self._column_name = column_name

    def configure(self, *arguments):
        pass

    @abstractmethod
    def check(self, data):
        pass
