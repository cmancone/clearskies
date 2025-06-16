from __future__ import annotations
from typing import Any, Callable, Iterator, Self, TYPE_CHECKING
from abc import abstractmethod
import re


from clearskies.functional import string
from clearskies.di import InjectableProperties, inject
from clearskies.query import Query, Sort, Condition, Join
from clearskies.autodoc.schema import Schema as AutoDocSchema
from clearskies.schema import Schema
if TYPE_CHECKING:
    from clearskies import Column
    from clearskies.backends import Backend

class Model(Schema, InjectableProperties):
    """
    A clearskies model.

    To be useable, a model class needs three things:

     1. Column definitions
     2. The name of the id column
     3. A backend
     4. A destination name (equivalent to a table name for SQL backends)

    """

    _previous_data: dict[str, Any] = {}
    _data: dict[str, Any] = {}
    _next_data: dict[str, Any] = {}
    _transformed_data: dict[str, Any] = {}
    _touched_columns: dict[str, bool] = {}
    _query: Query | None = None
    _query_executed: bool = False
    _count: int | None = None
    _next_page_data: dict[str, Any] | None = None

    id_column_name: str = ""
    backend: Backend = None # type: ignore

    _di = inject.Di()

    def __init__(self):
        if not self.id_column_name:
            raise ValueError(f"You must define the 'id_column_name' property for every model class, but this is missing for model '{self.__class__.__name__}'")
        if not isinstance(self.id_column_name, str):
            raise TypeError(f"The 'id_column_name' property of a model must be a string that specifies the name of the id column, but that is not the case for model '{self.__class__.__name__}'.")
        if not self.backend:
            raise ValueError(f"You must define the 'backend' property for every model class, but this is missing for model '{self.__class__.__name__}'")
        if not hasattr(self.backend, "documentation_pagination_parameters"):
            raise TypeError(f"The 'backend' property of a model must be an object that extends the clearskies.Backend class, but that is not the case for model '{self.__class__.__name__}'.")
        self._previous_data = {}
        self._data = {}
        self._next_data = {}
        self._transformed_data = {}
        self._touched_columns = {}
        self._query = None
        self._query_executed = False
        self._count = None
        self._next_page_data = None

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

    def supports_n_plus_one(self: Self):
        return self.backend.supports_n_plus_one #  type: ignore

    def __bool__(self: Self) -> bool:
        if self._query:
            return bool(self.__len__())

        return True if self._data else False

    def get_raw_data(self: Self) -> dict[str, Any]:
        self.no_queries()
        return self._data

    def set_raw_data(self: Self, data: dict[str, Any]) -> None:
        self.no_queries()
        self._data = {} if data is None else data
        self._transformed_data = {}

    def save(self: Self, data: dict[str, Any] | None = None, columns: dict[str, Column]={}, no_data=False) -> bool:
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
        self.no_queries()
        if not data and not self._next_data and not no_data:
            raise ValueError("You have to pass in something to save, or set no_data=True in your call to save/create.")
        if data and self._next_data:
            raise ValueError(
                "Save data was provided to the model class by both passing in a dictionary and setting new values on the column attributes.  This is not allowed.  You will have to use just one method of specifying save data."
            )
        if not data:
            data = {**self._next_data}
            self._next_data = {}

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

        self.set_raw_data(new_data)
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
        self.no_queries()
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
        self.no_queries()
        if key in data:
            return data[key]
        return getattr(self, key)

    def was_changed(self: Self, key: str) -> bool:
        """Returns True/False to denote if a column was changed in the last save"""
        self.no_queries()
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
        self.no_queries()
        return getattr(self.__class__, key).transform(self._previous_data.get(key))

    def delete(self: Self, except_if_not_exists=True) -> bool:
        self.no_queries()
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
            column.post_save(data, self, id)
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

    ##############################################################
    ### From here down is functionality related to list/search ###
    ##############################################################
    def has_query(self) -> bool:
        """
        Whether or not this model instance represents a query.
        """
        return bool(self._query)

    def get_query(self) -> Query:
        """
        Fetch the query object in the model
        """
        return self._query if self._query else Query(self.__class__)

    def as_query(self) -> Self:
        """
        Make the model queryable!

        This is used to remove the ambiguity of attempting execute a query against a model object that stores a record.

        The reason this exists is because the model class is used both to query as well as to operate on single records, which can cause
        subtle bugs if a developer accidentally confuses the two usages.  Consider the following (partial) example:

        ```
        def some_function(models):
            model = models.find("id=5")
            if model:
                models.save({"test":"example"})
            other_record = model.find("id=6")
        ```

        In the above example it seems likely that the intention was to use `model.save()`, not `models.save()`.  Similarly, the last line
        should be `models.find()`, not `model.find()`.  To minimize these kinds of issues, clearskies won't let you execute a query against
        an individual model record, nor will it let you execute a save against a model being used to make a query.  In both cases, you'll
        get an exception from clearskies, as the models track exactly how they are being used.

        In some rare cases though, you may want to start a new query aginst a model that represents a single record.  This is most common
        if you have a function that was passed an individual model, and you'd like to use it to fetch more records without having to
        inject the model class more generally.  That's where the `as_query()` method comes in.  It's basically just a way of telling clearskies
        "yes, I really do want to start a query using a model that represents a record".  So, for example:

        ```
        def some_function(models):
            model = models.find("id=5")
            more_models = model.where("test=example") # throws an exception.
            more_models = model.as_query().where("test=example") # works as expected.
        ```
        """
        new_model= self._di.build(self.__class__, cache=False)
        new_model.set_query(Query(self.__class__))
        return new_model

    def set_query(self, query: Query) -> Self:
        """
        Set the query object
        """
        self._query = query
        self._query_executed = False
        return self

    def with_query(self, query: Query) -> Self:
        return self._di.build(self.__class__, cache=False).set_query(query)

    def select(self: Self, select: str) -> Self:
        """
        Add some additional columns to the select part of the query.

        This method returns a new object with the updated query.  The original model object is unmodified.
        Multiple calls to this method add together.  The following:

        ```
        models.select("column_1 column_2").select("column_3")
        ```

        will select column_1, column_2, column_3 in the final query.
        """
        self.no_single_model()
        return self.with_query(self.get_query().add_select(select))

    def select_all(self: Self, select_all=True) -> Self:
        """
        Set whether or not to select all columns with the query.

        This method returns a new object with the updated query.  The original model object is unmodified.
        """
        self.no_single_model()
        return self.with_query(self.get_query().set_select_all(select_all))

    def where(self: Self, where: str | Condition) -> Self:
        """
        Adds the given condition to the query.

        This method returns a new object with the updated query.  The original model object is unmodified.

        Conditions should be an SQL-like string of the form [column][operator][value] with an optional table prefix.
        You can safely inject user input into the value.  The column name will also be checked against the searchable
        columns for the model class, and an exception will be thrown if the column doesn't exist or is not searchable.

        Multiple conditions are always joined with AND.  There is no explicit option for OR.  The closest is using an
        IN condition.

        Examples:

        ```
        for record in models.where("order_id=5").where("status IN ('ACTIVE','PENDING')").where("other_table.id=asdf"):
            print(record.id)
        ```
        """
        self.no_single_model()
        return self.with_query(self.get_query().add_where(where if isinstance(where, Condition) else Condition(where)))

    def join(self: Self, join: str) -> Self:
        """
        Adds a join clause to the query.
        """
        self.no_single_model()
        return self.with_query(self.get_query().add_join(Join(join)))

    def is_joined(self: Self, table_name: str, alias: str="") -> bool:
        """
        Check if a given table was already joined.

        If you provide an alias then it will also verify if the table was joined with the specific alias name.
        """
        for join in self.get_query().joins:
            if join.unaliased_table_name != table_name:
                continue

            if alias and join.alias != alias:
                continue

            return True
        return False

    def group_by(self: Self, group_by_column_name: str) -> Self:
        self.no_single_model()
        return self.with_query(self.get_query().set_group_by(group_by_column_name))

    def sort_by(
        self: Self,
        primary_column_name: str,
        primary_direction: str,
        primary_table_name: str="",
        secondary_column_name: str="",
        secondary_direction: str="",
        secondary_table_name: str="",
    ) -> Self:
        self.no_single_model()
        sort = Sort(primary_table_name, primary_column_name, primary_direction)
        secondary_sort = None
        if secondary_column_name and secondary_direction:
            secondary_sort = Sort(secondary_table_name, secondary_column_name, secondary_direction)
        return self.with_query(self.get_query().set_sort(sort, secondary_sort))

    def limit(self: Self, limit: int) -> Self:
        self.no_single_model()
        return self.with_query(self.get_query().set_limit(limit))

    def pagination(self: Self, **pagination_data) -> Self:
        self.no_single_model()
        error = self.backend.validate_pagination_data(pagination_data, str)
        if error:
            raise ValueError(
                f"Invalid pagination data for model {self.__class__.__name__} with backend "
                + f"{self.backend.__class__.__name__}. {error}"
            )
        return self.with_query(self.get_query().set_pagination(pagination_data))

    def find(self: Self, where: str | Condition) -> Self:
        """
        Returns the first model matching a given where condition.

        This is just shorthand for `models.where("column=value").find()`.  Example:

        ```
        model = models.find("column=value")
        print(model.id)
        ```
        """
        self.no_single_model()
        return self.where(where).first()

    def __len__(self: Self):
        self.no_single_model()
        if self._count is None:
            self._count = self.backend.count(self.get_query())
        return self._count

    def __iter__(self: Self) -> Iterator[Self]:
        self.no_single_model()
        self._next_page_data = {}
        raw_rows = self.backend.records(
            self.get_query(),
            next_page_data=self._next_page_data,
        )
        return iter([self.model(row) for row in raw_rows])

    def paginate_all(self: Self) -> list[Self]:
        """
        Loops through all available pages of results and returns a list of all models that match the query.

        NOTE: this loads up all records in memory before returning (e.g. it isn't using generators yet), so
        expect delays for large record sets.

        ```
        for model in models.where("column=value").paginate_all():
            print(model.id)
        """
        self.no_single_model()
        next_models = self.with_query(self.get_query())
        results = list(next_models.__iter__())
        next_page_data = next_models.next_page_data()
        while next_page_data:
            next_models = self.pagination(**next_page_data)
            results.extend(next_models.__iter__())
            next_page_data = next_models.next_page_data()
        return results

    def model(self: Self, data: dict[str, Any] = {}) -> Self:
        """
        Creates a new model object and populates it with the data in `data`.

        NOTE: the difference between this and `model.create` is that model.create() actually saves a record in the backend,
        while this method just creates a model object populated with the given data.
        """
        model = self._di.build(self.__class__, cache=False)
        model.set_raw_data(data)
        return model

    def create(self: Self, data: dict[str, Any] = {}, columns: dict[str, Column]={}, no_data=False) -> Self:
        """
        Creates a new record in the backend using the information in `data`.

        new_model = models.create({"column": "value"})
        """
        empty = self.model()
        empty.save(data, columns=columns, no_data=no_data)
        return empty

    def first(self: Self) -> Self:
        """
        Returns the first model matching the given query:

        ```
        model = models.where("column=value").sort_by("age", "DESC").first()
        print(model.id)
        ```
        """
        self.no_single_model()
        iter = self.__iter__()
        try:
            return iter.__next__()
        except StopIteration:
            return self.model()

    def allowed_pagination_keys(self: Self) -> list[str]:
        return self.backend.allowed_pagination_keys()

    def validate_pagination_data(self, kwargs: dict[str, Any], case_mapping: Callable[[str], str]) -> str:
        return self.backend.validate_pagination_data(kwargs, case_mapping)

    def next_page_data(self: Self):
        return self._next_page_data

    def documentation_pagination_next_page_response(self: Self, case_mapping: Callable) -> list[Any]:
        return self.backend.documentation_pagination_next_page_response(case_mapping)

    def documentation_pagination_next_page_example(self: Self, case_mapping: Callable) -> dict[str, Any]:
        return self.backend.documentation_pagination_next_page_example(case_mapping)

    def documentation_pagination_parameters(self: Self, case_mapping: Callable) -> list[tuple[AutoDocSchema, str]]:
        return self.backend.documentation_pagination_parameters(case_mapping)

    def no_queries(self) -> None:
        if self._query:
            raise ValueError("You attempted to save/read record data for a model being used to make a query.  This is not allowed, as it is typically a sign of a bug in your application code.")

    def no_single_model(self):
        if self._data:
            raise ValueError("You have attempted to execute a query against a model that represents an individual record.  This is not allowed, as it is typically a sign of a bug in your application code.  If this is intentional, call model.as_query() before executing your query.")


class ModelClassReference:
    @abstractmethod
    def get_model_class(self) -> type[Model]:
        pass
