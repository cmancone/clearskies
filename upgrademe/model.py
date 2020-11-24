from abc import ABC, abstractmethod


class Model(ABC):
    _data = None

    @property
    @abstractmethod
    def table_name(self):
        """ Return the name of the table that the model uses for data storage """
        pass

    def __getattr__(self, attribute_name):
        return self._data[attribute_name]

    @property
    def exists(self):
        return 'id' in self._data and self._data['id']

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data
