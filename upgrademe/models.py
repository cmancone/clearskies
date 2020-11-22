from abc import ABC, abstractmethod
from .model import Model
from .condition_parser import ConditionParser


class Models(ABC, ConditionParser):
    # The database connection
    cursor = None
    conditions = None
    sort = None
    parameters = None
    group_by = None

    def __init__(self, cursor):
        self.cursor = cursor
        self.conditions = []
        self.sort = []
        self.group_by = None
        self.parameters = []

    @property
    @abstractmethod
    def model_class(self):
        """ Return the model class that this models object will find/return instances of """
        pass

    def _clone(self):
        clone = self.__class__(self.cursor)
        clone.configuration = self.configuration
        return clone

    @property
    def configuration(self):
        return {
            'conditions': self.conditions,
            'sort': self.sort,
            'parameters': self.parameters,
            'group_by': self.group_by,
        }

    @configruation.setter
    def configuration(self, configuration):
        pass

    def table_name(self):
        """ Returns the name of the table for the model class """
        return self.model_class().table_name

    def find(self, condition):
        """ Returns the first model where {field}={value} """
        return self.clone().where_in_place(condition).first()
