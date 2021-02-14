from abc import ABC, abstractmethod


class Backend(ABC):
    @abstractmethod
    def update(self, id, data, model):
        pass

    @abstractmethod
    def create(self, data, model):
        pass

    @abstractmethod
    def delete(self, id):
        pass

    @abstractmethod
    def count(self, configuration):
        pass

    @abstractmethod
    def iterator(self, configuration):
        pass

    @abstractmethod
    def next(self, configuration):
        pass
