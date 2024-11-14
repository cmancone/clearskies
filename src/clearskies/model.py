from typing import Any, Dict, Optional, Union

from abc import abstractmethod
from collections import OrderedDict
from .functional import string
import re

try:
    from typing_extensions import Self
except ModuleNotFoundError:
    from typing import Self

from . import column_config


class Model:
    _columns = None
    _column_configs: Dict[str, column_config.ColumnConfig] = {}
    _previous_data: Dict[str, Any] = {}
    _data: Dict[str, Any] = {}
    _next_data: Dict[str, Any] = None
    _transformed_data: Dict[str, Any] = None
    _touched_columns: Dict[str, bool] = None
    id_column_name: str = ""

    def __init__(self: Self, backend, columns):
        self._backend = backend
        self._columns = columns
        self._transformed_data = {}
        self._previous_data = {}
        self._data = {}
        self._next_data = {}
        self._touched_columns = {}

        model_class = self.__class__
        if not self.id_column_name:
            raise ValueError(
                f"Error for model class '{model_class.__name__}': no value was specified for the 'id_column_name' property.  This is a required property."
            )
        column_configs = self.__class__.get_column_configs()
        if self.id_column_name not in column_configs:
            raise ValueError(
                f"Error for model class '{model_class.__name__}': the provided id_column_name, '{self.id_column_name}' does not correspond to a column for the model"
            )

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """
        Return the name of the destination that the model uses for data storage

        For SQL backends, this would return the table name.  Other backends will use this
        same function but interpret it in whatever way it makes sense.  For instance, an
        API backend may treat it as a URL (or URL path), an SQS backend may expect a queue
        URL, etc...

        By default this takes the class name, converts from title case to snake case, and then
        makes it plural.
        """
        singular = string.camel_case_to_snake_case(cls.__name__)
        if singular[-1] == "y":
            return singular[:-1] + "ies"
        if singular[-1] == "s":
            return singular + "es"
        return f"{singular}s"

    @classmethod
    def get_column_configs(cls: type[Self]) -> Dict[str, column_config.ColumnConfig]:
        """Returns an ordered dictionary with the configuration for the columns"""
        if cls._column_configs:
            return cls._column_configs

        column_configs: Dict[str, column_config.ColumnConfig] = {}
        for attribute_name in dir(cls):
            attribute = getattr(cls, attribute_name)
            if not isinstance(attribute, column_config.ColumnConfig):
                continue

            column_config.finalize_configuration(cls, attribute_name)
            column_configs[attribute_name] = column_config

        cls._column_configs = column_configs
        return cls.column_configs

    def columns(self: Self, overrides=None) -> Dict[str, Any]:
        """
        Returns a dictionary with the column implementors.

        The difference between this function and model.column_configs is that this returns
        the column implementors (e.g. clearskies.columns.implementors) rather than the column
        config objects (which are defined via model parameters).

        The column implementors are used throughout the save/load cycle.
        """
        model_class = self.__class__
        # no caching if we have overrides
        if overrides is not None:
            return self._columns.configure(self.all_columns(), self.__class__, overrides=overrides)

        if self._configured_columns is None:
            self._configured_columns = self._columns.configure(self.all_columns(), self.__class__)
        return self._configured_columns

    def supports_n_plus_one(self: Self):
        return self._backend.supports_n_plus_one

    def get(self: Self, column_name, silent=False):
        if not self.exists:
            return None

        return self.get_transformed_from_data(column_name, self._data, silent=silent)

    def get_transformed_from_data(self: Self, column_name, data, cache=True, check_providers=True, silent=False):
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
            value = (
                self._backend.column_from_backend(self.columns()[column_name], data[column_name])
                if column_name in self.columns()
                else data[column_name]
            )

        if cache:
            self._transformed[column_name] = value
        return value

    def __bool__(self: Self) -> bool:
        return True if (self.id_column_name in self._data and self._data[self.id_column_name]) else False

    def get_raw_data(self: Self) -> Dict[str, Any]:
        return self._data

    def set_raw_data(self: Self, data: Dict[str, Any]) -> None
        self._data = {} if data is None else data

    def save(self: Self, data: Optional[Dict[str, Any]]=None, columns=None) -> bool:
        """
        Save data to the database and update the model!

        Executes an update if the model corresponds to a record already, or an insert if not.

        There are two supported flows.  One is to pass in a dictionary of data to save:

        ```
        model.save({
            "some_column": "New Value",
            "another_column": 5,
        })
        ```

        And the other is to set new values on the columns attributes and then call save without data:

        ```
        model.some_column = "New Value"
        model.another_column = 5
        model.save()
        ```

        You cannot combine these methods.  If you set a value on a column attribute and also pass
        in a dictionary of data to the save, then an exception will be raised.
        """
        if not len(data) and not len(self._next_data):
            raise ValueError("You have to pass in something to save!")
        if len(data) and len(self._next_data):
            raise ValueError("Save data was provided to the model class by both passing in a dictionary and setting new values on the column attributes.  This is not allowed.  You will have to use just one method of specifying save data.")
        if not len(data):
            data = {**self._next_data}

        save_columns = self.columns()
        if columns is not None:
            for column in columns.values():
                save_columns[column.name] = column

        old_data = self.data
        data = self.columns_pre_save(data, save_columns)
        data = self.pre_save(data)
        if data is None:
            raise ValueError("pre_save forgot to return the data array!")

        [to_save, temporary_data] = self.columns_to_backend(data, save_columns)
        to_save = self.to_backend(to_save, save_columns)
        if self.exists:
            new_data = self._backend.update(self._data[self.id_column_name], to_save, self)
        else:
            new_data = self._backend.create(to_save, self)
        id = self._backend.column_from_backend(save_columns[self.id_column_name], new_data[self.id_column_name])

        # if we had any temporary columns add them back in
        new_data = {
            **temporary_data,
            **new_data,
        }

        data = self.columns_post_save(data, id, save_columns)
        self.post_save(data, id)

        self.data = new_data
        self._transformed = {}
        self._previous_data = old_data
        self._touched_columns = list(data.keys())

        self.columns_save_finished(save_columns)
        self.save_finished()

        return True

    def is_changing(self: Self, key: str, data: Dict[str, Any]) -> bool:
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

    def latest(self: Self, key: str, data: Dict[str, Any]) -> Any:
        """
        Returns the 'latest' value for a column during the save operation

        Returns either the column value from the data dictionary or the current value stored in the model
        Basically, shorthand for the optimized version of:  `data.get(key, default=getattr(self, key))` (which is
        less than ideal because it always builds the default value, even when not necessary)

        Pass in the name of the column to check and the data dictionary from the save in progress
        """
        if key in data:
            return data[key]
        return getattr(self, key)

    def was_changed(self: Self, key: str) -> bool:
        """Returns True/False to denote if a column was changed in the last save"""
        if self._previous_data is None:
            raise ValueError("was_changed was called before a save was finished - you must save something first")
        if key not in self._touched_columns:
            return False

        has_old_value = bool(self._previous_data.get(key))
        has_new_value = bool(self._data.get(key))

        if has_new_value != has_old_value:
            return True

        if not has_old_value:
            return False

        columns = self.columns()
        new_value = self._data[key]
        old_value = self._previous_data[key]
        if key not in columns:
            return old_value != new_value
        return not columns[key].values_match(old_value, new_value)

    def previous_value(self: Self, key: str):
        return self.get_transformed_from_data(key, self._previous_data, cache=False, check_providers=False, silent=True)

    def delete(self: Self, except_if_not_exists=True) -> bool:
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

    def columns_pre_save(self: Self, data: Dict[str, Any], columns) -> Dict[str, Any]:
        """Uses the column information present in the model to make any necessary changes before saving"""
        for column in columns.values():
            data = column.pre_save(data, self)
            if data is None:
                raise ValueError(
                    f"Column {column.name} of type {column.__class__.__name__} did not return any data for pre_save"
                )
        return data

    def pre_save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        A hook to extend so you can provide additional pre-save logic as needed

        It is passed in the data being saved and it should return the same data with adjustments as needed
        """
        return data

    def columns_to_backend(self: Self, data: Dict[str, Any], columns) -> Any:
        backend_data = {**data}
        temporary_data = {}
        for column in columns.values():
            if column.is_temporary:
                if column.name in backend_data:
                    temporary_data[column.name] = backend_data[column.name]
                    del backend_data[column.name]
                continue

            backend_data = self._backend.column_to_backend(column, backend_data)
            if backend_data is None:
                raise ValueError(
                    f"Column {column.name} of type {column.__class__.__name__} did not return any data for to_database"
                )

        return [backend_data, temporary_data]

    def to_backend(self: Self, data: Dict[str, Any], columns) -> Dict[str, Any]:
        return data

    def columns_post_save(self: Self, data: Dict[str, Any], id: Union[str, int], columns) -> Dict[str, Any]:
        """Uses the column information present in the model to make additional changes as needed after saving"""
        for column in columns.values():
            data = column.post_save(data, self, id)
            if data is None:
                raise ValueError(
                    f"Column {column.name} of type {column.__class__.__name__} did not return any data for post_save"
                )
        return data

    def columns_save_finished(self: Self, columns) -> None:
        """Calls the save_finished method on all of our columns"""
        for column in columns.values():
            column.save_finished(self)

    def post_save(self: Self, data: Dict[str, Any], id: Union[str, int]) -> None:
        """
        A hook to extend so you can provide additional pre-save logic as needed

        It is passed in the data being saved as well as the id.  It should take action as needed and then return
        either the original data array or an adjusted one if appropriate.
        """
        pass

    def pre_save(self: Self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        A hook to extend so you can provide additional pre-save logic as needed

        It is passed in the data being saved and it should return the same data with adjustments as needed
        """
        return data

    def save_finished(self: Self) -> None:
        """
        A hook to extend so you can provide additional logic after a save operation has fully completed

        It has no retrun value and is passed no data.  By the time this fires the model has already been
        updated with the new data.  You can decide on the necessary actions using the `was_changed` and
        the `previous_value` functions.
        """
        pass

    def columns_pre_delete(self: Self, columns) -> None:
        """Uses the column information present in the model to make any necessary changes before deleting"""
        for column in columns.values():
            column.pre_delete(self)

    def pre_delete(self: Self) -> None:
        """
        A hook to extend so you can provide additional pre-delete logic as needed
        """
        pass

    def columns_post_delete(self: Self, columns) -> None:
        """Uses the column information present in the model to make any necessary changes after deleting"""
        for column in columns.values():
            column.post_delete(self)

    def post_delete(self: Self) -> None:
        """
        A hook to extend so you can provide additional post-delete logic as needed
        """
        pass

    def where_for_request(self: Self, models: Self, routing_data: Dict[str, str], authorization_data: Dict[str, Any], input_output: Any, overrides=None) -> Self:
        """
        A hook to automatically apply filtering whenever the model makes an appearance in a get/update/list/search handler.
        """
        for column in self.columns(overrides=overrides).values():
            models = column.where_for_request(models, routing_data, authorization_data, input_output)
        return models
