from abc import ABC, abstractmethod
from collections import OrderedDict
from .column_types import Integer
import re


class Model(ABC):
    _columns = None
    _configured_columns = None
    _backend = None
    _data = None
    _transformed = None

    def __init__(self, backend, columns):
        self._backend = backend
        self._columns = columns
        self._transformed = {}
        self._data = {}

    def _camel_case_to_snake_case(self, string):
        return re.sub(
            '([a-z0-9])([A-Z])', r'\1_\2',
            re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)
        ).lower()

    @property
    def table_name(self):
        """ Return the name of the table that the model uses for data storage """
        singular = self._camel_case_to_snake_case(self.__class__.__name__)
        if singular[-1] == 'y':
            return singular[:-1] + 'ies'
        if singular[-1] == 's':
            return singular + 'es'
        return f'{singular}s'

    @abstractmethod
    def columns_configuration(self):
        """ Returns an ordered dictionary with the configuration for the columns """
        pass

    def all_columns(self):
        default = OrderedDict([('id', {'class': Integer})])
        default.update(self.columns_configuration())
        return default

    def columns(self, overrides=None):
        # no caching if we have overrides
        if overrides is not None:
            return self._columns.configure(self.all_columns(), self.__class__, overrides=overrides)

        if self._configured_columns is None:
            self._configured_columns = self._columns.configure(self.all_columns(), self.__class__)
        return self._configured_columns

    def __getitem__(self, column_name):
        return self.__getattr__(column_name)

    def __getattr__(self, column_name):
        # this should be adjusted to only return None for empty records if the column name corresponds
        # to an actual column in the table.
        if not self.exists:
            return None

        # everything in self._data came directly out of the database, but we don't want to send that off.
        # instead, the corresponding column has an opportunity to make changes as needed.  Moreover,
        # it could be that the requested column_name doesn't even exist directly in self._data, but
        # can be provided by a column.  Therefore, we're going to do some work to fulfill the request,
        # raise an Error if we *really* can't fulfill it, and store the results in self._transformed
        # as a simple local cache (self._transformed is cleared during a save operation)
        if column_name not in self._transformed:
            columns = self.columns()
            if column_name not in self._data or self._data[column_name] is None:
                for column in columns.values():
                    if column.can_provide(column_name):
                        self._transformed[column_name] = column.provide(self._data, column_name)
                        break
                if column_name not in self._transformed and column_name not in self._data:
                    raise KeyError(f"Unknown column '{column_name}' requested from model '{self.__class__.__name__}'")

            else:
                self._transformed[column_name] = \
                    self.columns()[column_name].from_database(self._data[column_name]) \
                    if column_name in self.columns() \
                    else self._data[column_name]

        return self._transformed.get(column_name, None)


    @property
    def exists(self):
        return True if ('id' in self._data and self._data['id']) else False

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = {} if data is None else data

    def save(self, data):
        """
        Save data to the database and update the model!

        Executes an update if the model corresponds to a record already, or an insert if not
        """
        if not len(data):
            raise ValueError("You have to pass in something to save!")
        columns = self.columns()

        data = self.columns_pre_save(data, columns)
        data = self.pre_save(data)
        if data is None:
            raise ValueError("pre_save forgot to return the data array!")

        to_save = self._to_backend(data, columns)
        if self.exists:
            new_data = self._backend.update(self.id, to_save, self)
        else:
            new_data = self._backend.create(to_save, self)
        id = columns['id'].from_database(new_data['id'])

        data = self.columns_post_save(data, id, columns)
        data = self.post_save(data, id)
        if data is None:
            raise ValueError("post_save forgot to return the data array!")

        self._data = new_data
        self._transformed = {}
        return True

    def delete(self, except_if_not_exists=True):
        if not self.exists:
            if except_if_not_exists:
                raise ValueError("Cannot delete model that already exists")
            return True

        columns = self.columns()
        self.columns_pre_delete(columns)
        self.pre_delete()

        self._backend.delete(self.id, self)

        self.columns_post_delete(columns)
        self.post_delete()
        return True

    def columns_pre_save(self, data, columns):
        """ Uses the column information present in the model to make any necessary changes before saving """
        for column in columns.values():
            data = column.pre_save(data, self)
            if data is None:
                raise ValueError(
                    f'Column {column.name} of type {column.__class__.__name__} did not return any data for pre_save'
                )
        return data

    def pre_save(self, data):
        """
        A hook to extend so you can provide additional pre-save logic as needed

        It is passed in the data being saved and it should return the same data with adjustments as needed
        """
        return data

    def _to_backend(self, data, columns):
        backend_data = {**data}
        for column in columns.values():
            backend_data = column.to_database(backend_data)
            if backend_data is None:
                raise ValueError(
                    f'Column {column.name} of type {column.__class__.__name__} did not return any data for to_database'
                )

        return backend_data

    def columns_post_save(self, data, id, columns):
        """ Uses the column information present in the model to make additional changes as needed after saving """
        for column in columns.values():
            data = column.post_save(data, self, id)
            if data is None:
                raise ValueError(
                    f'Column {column.name} of type {column.__class__.__name__} did not return any data for post_save'
                )
        return data

    def post_save(self, data, id):
        """
        A hook to extend so you can provide additional pre-save logic as needed

        It is passed in the data being saved as well as the id.  It should take action as needed and then return
        either the original data array or an adjusted one if appropriate.
        """
        return data

    def pre_save(self, data):
        """
        A hook to extend so you can provide additional pre-save logic as needed

        It is passed in the data being saved and it should return the same data with adjustments as needed
        """
        return data

    def columns_pre_delete(self, columns):
        """ Uses the column information present in the model to make any necessary changes before deleting """
        for column in columns.values():
            column.pre_delete(self)

    def pre_delete(self):
        """
        A hook to extend so you can provide additional pre-delete logic as needed
        """
        pass

    def columns_post_delete(self, columns):
        """ Uses the column information present in the model to make any necessary changes after deleting """
        for column in columns.values():
            column.post_delete(self)

    def post_delete(self):
        """
        A hook to extend so you can provide additional post-delete logic as needed
        """
        pass
