from abc import abstractmethod
from collections import OrderedDict
from .column_types import UUID
from .functional import string
import re
from .models import Models
class Model(Models):
    _configured_columns = None
    _data = None
    _previous_data = None
    _transformed = None
    id_column_name = 'id'

    def __init__(self, backend, columns):
        super().__init__(backend, columns)
        self._transformed = {}
        self._data = {}
        self._previous_data = None

    def model_class(self):
        """
        Return the model class that this models object will find/return instances of

        This is needed by the models class
        """
        return self.__class__

    @classmethod
    def table_name(cls):
        """ Return the name of the table that the model uses for data storage """
        singular = string.camel_case_to_snake_case(cls.__name__)
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
        default = OrderedDict([(self.id_column_name, {'class': UUID})])
        default.update(self.columns_configuration())
        return default

    def columns(self, overrides=None):
        # no caching if we have overrides
        if overrides is not None:
            return self._columns.configure(self.all_columns(), self.__class__, overrides=overrides)

        if self._configured_columns is None:
            self._configured_columns = self._columns.configure(self.all_columns(), self.__class__)
        return self._configured_columns

    def supports_n_plus_one(self):
        return self._backend.supports_n_plus_one

    def __getitem__(self, column_name):
        return self.__getattr__(column_name)

    def __getattr__(self, column_name):
        # this should be adjusted to only return None for empty records if the column name corresponds
        # to an actual column in the table.
        if not self.exists:
            return None

        return self.get_transformed_from_data(column_name, self._data)

    def get(self, column_name, silent=False):
        if not self.exists:
            return None

        return self.get_transformed_from_data(column_name, self._data, silent=silent)

    def get_transformed_from_data(self, column_name, data, cache=True, check_providers=True, silent=False):
        if cache and column_name in self._transformed:
            return self._transformed[column_name]

        # everything in self._data came directly out of the database, but we don't want to send that off.
        # instead, the corresponding column has an opportunity to make changes as needed.  Moreover,
        # it could be that the requested column_name doesn't even exist directly in self._data, but
        # can be provided by a column.  Therefore, we're going to do some work to fulfill the request,
        # raise an Error if we *really* can't fulfill it, and store the results in self._transformed
        # as a simple local cache (self._transformed is cleared during a save operation)
        columns = self.columns()
        value = None
        if (column_name not in data or data[column_name] is None) and check_providers:
            for column in columns.values():
                if column.can_provide(column_name):
                    value = column.provide(data, column_name)
                    break
            if column_name not in data and value is None:
                if not silent:
                    raise KeyError(f"Unknown column '{column_name}' requested from model '{self.__class__.__name__}'")
                return None
        else:
            value = self._backend.column_from_backend(self.columns()[column_name], data[column_name]) \
                if column_name in self.columns() \
                else data[column_name]

        if cache:
            self._transformed[column_name] = value
        return value

    @property
    def exists(self):
        return True if (self.id_column_name in self._data and self._data[self.id_column_name]) else False

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

        old_data = self.data
        data = self.columns_pre_save(data, columns)
        data = self.pre_save(data)
        if data is None:
            raise ValueError("pre_save forgot to return the data array!")

        to_save = self.columns_to_backend(data, columns)
        to_save = self.to_backend(to_save, columns)
        if self.exists:
            new_data = self._backend.update(self._data[self.id_column_name], to_save, self)
        else:
            new_data = self._backend.create(to_save, self)
        id = self._backend.column_from_backend(columns[self.id_column_name], new_data[self.id_column_name])

        data = self.columns_post_save(data, id, columns)
        self.post_save(data, id)

        self.data = new_data
        self._transformed = {}
        self._previous_data = old_data

        self.columns_save_finished(columns)
        self.save_finished()

        return True

    def is_changing(self, key, data):
        """
        Returns True/False to denote if the given column is being modified by the active save operation

        Pass in the name of the column to check and the data dictionary from the save in progress
        """
        has_old_value = key in self._data
        has_new_value = key in data

        if not has_new_value:
            return False
        if not has_old_value:
            return True

        return self.__getattr__(key) != data[key]

    def latest(self, key, data):
        """
        Returns the 'latest' value for a column during the save operation

        Returns either the column value from the data dictionary or the current value stored in the model
        Basically, shorthand for the optimized version of:  `data.get(key, default=getattr(self, key))` (which is
        less than ideal because it always builds the default value, even when not necessary)

        Pass in the name of the column to check and the data dictionary from the save in progress
        """
        if key in data:
            return data[key]
        return self.__getattr__(key)

    def was_changed(self, key):
        """ Returns True/False to denote if a column was changed in the last save """
        if self._previous_data is None:
            raise ValueError("was_changed was called before a save was finished - you must save something first")

        has_old_value = key in self._previous_data
        has_new_value = key in self._data

        if has_new_value != has_old_value:
            return True

        if not has_old_value:
            return False

        return self.__getattr__(key) != self._previous_data[key]

    def previous_value(self, key):
        return self.get_transformed_from_data(key, self._previous_data, cache=False, check_providers=False, silent=True)

    def delete(self, except_if_not_exists=True):
        if not self.exists:
            if except_if_not_exists:
                raise ValueError("Cannot delete model that already exists")
            return True

        columns = self.columns()
        self.columns_pre_delete(columns)
        self.pre_delete()

        self._backend.delete(self._data[self.id_column_name], self)

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

    def columns_to_backend(self, data, columns):
        backend_data = {**data}
        for column in columns.values():
            if column.is_temporary and column.name in backend_data:
                del backend_data[column.name]
                continue

            backend_data = self._backend.column_to_backend(column, backend_data)
            if backend_data is None:
                raise ValueError(
                    f'Column {column.name} of type {column.__class__.__name__} did not return any data for to_database'
                )

        return backend_data

    def to_backend(self, data, columns):
        return data

    def columns_post_save(self, data, id, columns):
        """ Uses the column information present in the model to make additional changes as needed after saving """
        for column in columns.values():
            data = column.post_save(data, self, id)
            if data is None:
                raise ValueError(
                    f'Column {column.name} of type {column.__class__.__name__} did not return any data for post_save'
                )
        return data

    def columns_save_finished(self, columns):
        """ Calls the save_finished method on all of our columns """
        for column in columns.values():
            column.save_finished(self)

    def post_save(self, data, id):
        """
        A hook to extend so you can provide additional pre-save logic as needed

        It is passed in the data being saved as well as the id.  It should take action as needed and then return
        either the original data array or an adjusted one if appropriate.
        """
        pass

    def pre_save(self, data):
        """
        A hook to extend so you can provide additional pre-save logic as needed

        It is passed in the data being saved and it should return the same data with adjustments as needed
        """
        return data

    def save_finished(self):
        """
        A hook to extend so you can provide additional logic after a save operation has fully completed

        It has no retrun value and is passed no data.  By the time this fires the model has already been
        updated with the new data.  You can decide on the necessary actions using the `was_changed` and
        the `previous_value` functions.
        """
        pass

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
