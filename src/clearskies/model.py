from __future__ import annotations
from typing import Any, Self, TYPE_CHECKING
from abc import abstractmethod
from collections import OrderedDict
import re


from clearskies.functional import string
if TYPE_CHECKING:
    from clearskies import Column


class Model:
    """
    A clearskies model.

    To be useable, a model class needs three things:

     1. Column definitions
     2. The name of the id column
     3. A backend

    All of these are provided as attributes.  The columns all come from the `clearskies.columns` module.

    """

    _columns: dict[str, Column] = {}
    _previous_data: dict[str, Any] = {}
    _data: dict[str, Any] = {}
    _next_data: dict[str, Any] = {}
    _transformed_data: dict[str, Any] = {}
    _touched_columns: dict[str, bool] = {}
    id_column_name: str = ""

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
    def get_columns(cls: type[Self], overrides: dict[str, Column]={}) -> dict[str, Column]:
        """
        Returns an ordered dictionary with the configuration for the columns

        Generally, this method is meant for internal use.  It just pulls the column configuration
        information out of class attributes.  It doesn't return the fully prepared columns,
        so you probably can't use the return value of this function.  For that, see
        `model.columns()`.
        """
        # no caching if we have overrides
        overrides = {**overrides}
        if cls._columns and not overrides:
            return cls._columns

        columns: dict[str, Column] = {}
        for attribute_name in dir(cls):
            attribute = getattr(cls, attribute_name)
            # use duck typing instead of isinstance to decide which attribute is a column.
            # We have to do this to avoid circular imports.
            if not hasattr(attribute, "setable") and not hasattr(attribute, "default"):
                continue

            if attribute_name in overrides:
                columns[attribute_name] = overrides[attribute_name]
                del overrides[attribute_name]
            attribute.finalize_configuration(cls, attribute_name)
            columns[attribute_name] = attribute

        for (attribute_name, column) in overrides.items():
            columns[attribute_name] = column  # type: ignore

        if not overrides:
            cls._columns = columns
        return columns

    def supports_n_plus_one(self: Self):
        return self.backend.supports_n_plus_one #  type: ignore

    def __bool__(self: Self) -> bool:
        return True if (self.id_column_name in self._data and self._data[self.id_column_name]) else False

    def get_raw_data(self: Self) -> dict[str, Any]:
        return self._data

    def set_raw_data(self: Self, data: dict[str, Any]) -> None:
        self._data = {} if data is None else data

    def save(self: Self, data: dict[str, Any] | None = None, columns: dict[str, Column]={}) -> bool:
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
        if not data and not self._next_data:
            raise ValueError("You have to pass in something to save!")
        if data and self._next_data:
            raise ValueError(
                "Save data was provided to the model class by both passing in a dictionary and setting new values on the column attributes.  This is not allowed.  You will have to use just one method of specifying save data."
            )
        if not data:
            data = {**self._next_data}

        save_columns = self.get_columns()
        if columns is not None:
            for column in columns.values():
                save_columns[column.name] = column

        old_data = self.get_raw_data()
        data = self.columns_pre_save(data, save_columns)
        data = self.pre_save(data)
        if data is None:
            raise ValueError("pre_save forgot to return the data array!")

        [to_save, temporary_data] = self.columns_to_backend(data, save_columns)
        to_save = self.to_backend(to_save, save_columns)
        if self:
            new_data = self.backend.update(self._data[self.id_column_name], to_save, self)  # type: ignore
        else:
            new_data = self.backend.create(to_save, self)  # type: ignore
        id = self.backend.column_from_backend(save_columns[self.id_column_name], new_data[self.id_column_name])  # type: ignore

        # if we had any temporary columns add them back in
        new_data = {
            **temporary_data,
            **new_data,
        }

        data = self.columns_post_save(data, id, save_columns)
        self.post_save(data, id)

        self.data = new_data
        self._transformed_data = {}
        self._previous_data = old_data
        self._touched_columns = {key: True for key in data.keys()}

        self.columns_save_finished(save_columns)
        self.save_finished()

        return True

    def is_changing(self: Self, key: str, data: dict[str, Any]) -> bool:
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

        return getattr(self, key) != data[key]

    def latest(self: Self, key: str, data: dict[str, Any]) -> Any:
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

        columns = self.get_columns()
        new_value = self._data[key]
        old_value = self._previous_data[key]
        if key not in columns:
            return old_value != new_value
        return not columns[key].values_match(old_value, new_value)

    def previous_value(self: Self, key: str):
        return getattr(self.__class__, key).transform(self._previous_data.get(key))

    def delete(self: Self, except_if_not_exists=True) -> bool:
        if not self:
            if except_if_not_exists:
                raise ValueError("Cannot delete model that already exists")
            return True

        columns = self.get_columns()
        self.columns_pre_delete(columns)
        self.pre_delete()

        self.backend.delete(self._data[self.id_column_name], self)  # type: ignore

        self.columns_post_delete(columns)
        self.post_delete()
        return True

    def columns_pre_save(self: Self, data: dict[str, Any], columns) -> dict[str, Any]:
        """Uses the column information present in the model to make any necessary changes before saving"""
        for column in columns.values():
            data = column.pre_save(data, self)
            if data is None:
                raise ValueError(
                    f"Column {column.name} of type {column.__class__.__name__} did not return any data for pre_save"
                )
        return data

    def columns_to_backend(self: Self, data: dict[str, Any], columns) -> Any:
        backend_data = {**data}
        temporary_data = {}
        for column in columns.values():
            if column.is_temporary:
                if column.name in backend_data:
                    temporary_data[column.name] = backend_data[column.name]
                    del backend_data[column.name]
                continue

            backend_data = self.backend.column_to_backend(column, backend_data)  # type: ignore
            if backend_data is None:
                raise ValueError(
                    f"Column {column.name} of type {column.__class__.__name__} did not return any data for to_database"
                )

        return [backend_data, temporary_data]

    def to_backend(self: Self, data: dict[str, Any], columns) -> dict[str, Any]:
        return data

    def columns_post_save(self: Self, data: dict[str, Any], id: str | int, columns) -> dict[str, Any]:
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

    def post_save(self: Self, data: dict[str, Any], id: str | int) -> None:
        """
        A hook to extend so you can provide additional pre-save logic as needed

        It is passed in the data being saved as well as the id.  It should take action as needed and then return
        either the original data array or an adjusted one if appropriate.
        """
        pass

    def pre_save(self: Self, data: dict[str, Any]) -> dict[str, Any]:
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

    def columns_pre_delete(self: Self, columns: dict[str, Column]) -> None:
        """Uses the column information present in the model to make any necessary changes before deleting"""
        for column in columns.values():
            column.pre_delete(self)

    def pre_delete(self: Self) -> None:
        """
        A hook to extend so you can provide additional pre-delete logic as needed
        """
        pass

    def columns_post_delete(self: Self, columns: dict[str, Column]) -> None:
        """Uses the column information present in the model to make any necessary changes after deleting"""
        for column in columns.values():
            column.post_delete(self)

    def post_delete(self: Self) -> None:
        """
        A hook to extend so you can provide additional post-delete logic as needed
        """
        pass

    def where_for_request(
        self: Self,
        models: Self,
        routing_data: dict[str, str],
        authorization_data: dict[str, Any],
        input_output: Any,
        overrides: dict[str, Column]={},
    ) -> Self:
        """
        A hook to automatically apply filtering whenever the model makes an appearance in a get/update/list/search handler.
        """
        for column in self.get_columns(overrides=overrides).values():
            models = column.where_for_request(models, routing_data, authorization_data, input_output)  # type: ignore
        return models
