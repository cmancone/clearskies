from __future__ import annotations
from typing import Any, overload, Callable, Self, TYPE_CHECKING, Type

import clearskies.di
import clearskies.model
import clearskies.typing
import clearskies.configurable
import clearskies.configs.actions
import clearskies.configs.boolean
import clearskies.configs.select
import clearskies.configs.string
import clearskies.configs.string_or_callable
import clearskies.configs.validators
from clearskies.autodoc.schema import Schema as AutoDocSchema
from clearskies.autodoc.schema import String as AutoDocString
from clearskies.query.condition import Condition, ParsedCondition
from clearskies.validator import Validator
import clearskies.parameters_to_properties

if TYPE_CHECKING:
    from clearskies import Model

class Column(clearskies.configurable.Configurable, clearskies.di.InjectableProperties):
    """
    The base column.

    This class (well, the children that extend it) are used to define the columns
    that exist in a given model class.  See the note on the columns module itself for full
    details of what that looks like.

    These objects themselves don't ever store data that is specifc to a model because
    of their lifecycle - they are bound to the model *class*, not to an individual model
    instance.  Thus, any information stored in the column config will be shared by
    all instances of that model.  Instead, actual model data is always stored in the model.
    """

    """
    The column class gets the full DI container, because it does a lot of object building itself
    """
    di = clearskies.di.inject.Di()

    """
    A default value to set for this column.

    The default is only used when creating a record for the first time, and only if
    a value for this column has not been set.
    """
    default = clearskies.configs.string.String(default=None)

    """
    A value to set for this column during a save operation.

    Unlike the default value, a setable value is always set during a save.
    """
    setable = clearskies.configs.string_or_callable.StringOrCallable(default=None)

    """
    Whether or not this column can be converted to JSON and included in an API response.
    """
    is_readable = clearskies.configs.boolean.Boolean(default=True)

    """
    Whether or not this column can be set via an API call.
    """
    is_writeable = clearskies.configs.boolean.Boolean(default=True)

    """
    Whether or not it is possible to search by this column
    """
    is_searchable = clearskies.configs.boolean.Boolean(default=True)

    """
    Whether or not this column is temporary.  A temporary column is not persisted to the backend.
    """
    is_temporary = clearskies.configs.boolean.Boolean(default=False)

    """
    Validators to use when checking the input for this column during write operations from the API.

    Keep in mind that the validators are only checked when the column is exposed via a supporting handler.
    You can still set whatever values you want when saving the model directly, e.g. `model.save(...)`
    """
    validators = clearskies.configs.validators.Validators(default=[])

    """
    Actions to take during the pre-save step of the save process if the column has changed in the save.

    Pre-save happens before the data is persisted to the backend.  Actions/callables in
    this step can return a dictionary of additional data to include in the save operation.

    Since the save hasn't completed, any data in the model itself reflects the model before the save
    operation started.

    Callables and actions can request any dependencies provided by the DI system.  In addition, they can request
    two named parameters:

     1. `model` - the model involved in the save operation
     2. `data` - the new data being saved

    The `is_changing` and `latest` methods on the model class are useful here, so give them a read.
    """
    on_change_pre_save = clearskies.configs.actions.Actions(default=[])

    """
    Actions to take during the post-save step of the process if the column has changed in the save.

    Post-save happens after the data is persisted to the backend but before the full save process has finished.
    Since the data has been persisted to the backend,any data returned by the callables/actions will be ignored.
    If you need to make data changes you'll have to execute a separate save operation.

    Since the save hasn't finished, the model is not yet updated with the new data, and
    any data you fetch out of the model will refelect the data in the model before the save started.

    Callables and actions can request any dependencies provided by the DI system.  In addition, they can request
    two named parameters:

     1. `model` - the model involved in the save operation
     2. `data` - the new data being saved

    The `is_changing` and `latest` methods on the model class are useful here, so give them a read.
    """
    on_change_post_save = clearskies.configs.actions.Actions(default=[])

    """
    Actions to take during the save-finished step of the save process if the column has changed in the save.

    Save-finished happens after the save process has completely finished and the model is updated with
    the final data.  Any data returned by these actions will be ignored, since the save has already finished.
    If you need to make data changes you'll have to execute a separate save operation.

    Callables and actions can request any dependencies provided by the DI system.  In addition, they can request
    the following parameter:

     1. `model` - the model involved in the save operation

    Unlike pre_save and post_save, `data` is not provided because this data has already been merged into the
    model.  To understand more about the save operation, use methods like `was_changed` and `previous_value`.

    """
    on_change_save_finished = clearskies.configs.actions.Actions(default=[])

    """
    Use in conjunction with `created_by_source_type` to have this column automatically populated by data from an HTTP request.

    So, for instance, setting `created_by_source_type` to `authorization_data` and setting this to `email`
    will result in the email value from the authorization data being persisted into this column when the
    record is saved.

    NOTE: this is sometimes best set as a column override on an API handler definition, rather than directly
    on the model itself.  The reason is because the authorization data and header information is typically
    only available during an HTTP request, so if you set this on the model level, you'll get an error
    if you try to make saves to the model in a context where authorization data and/or headers don't exist.
    """
    created_by_source_key = clearskies.configs.string.String(default="")

    """
    Use in conjunction with `created_by_source_key` to have this column automatically populated by data from ann HTTP request.

    So, for instance, setting this to `authorization_data` and setting `created_by_source_key` to `email`
    will result in the email value from the authorization data being persisted into this column when the
    record is saved.

    NOTE: this is sometimes best set as a column override on an API handler definition, rather than directly
    on the model itself.  The reason is because the authorization data and header information is typically
    only available during an HTTP request, so if you set this on the model level, you'll get an error
    if you try to make saves to the model in a context where authorization data and/or headers don't exist.
    """
    created_by_source_type = clearskies.configs.select.Select(["authorization_data", "http_header", "routing_data", ""], default="")

    """
    If True, and the key requested via created_by_source_key doesn't exist in the designated source, an error will be raised.
    """
    created_by_source_strict = clearskies.configs.boolean.Boolean(default=True)

    """ The model class this column is associated with. """
    model_class = clearskies.configs.ModelClass()

    """ The name of this column. """
    name = clearskies.configs.string.String()

    """
    Simple flag to denote if the column is unique or not.

    This is an internal cache.  Use column.is_unique instead.
    """
    _is_unique = False

    """
    Specify if this column has additional functionality to solve the n+1 problem.

    Relationship columns may fetch data from additional tables when outputting results, but by default they
    end up making an additional query for every record (in order to grab related data).  This is called the
    n+1 problem - a query may fetch 10 records, and then make 10 individual additional queries to select
    related data for each record (which obviously hampers performance).  The solution to this (when using
    sql-like backends) is to add additional joins to the original query so that the data can all be fetched
    at once.  Columns that are subject to this issue can set this flag to True and then  define the
    `configure_n_plus_one` method to add the necessary joins.  This method will be called as needed.
    """
    wants_n_plus_one = False

    """
    Simple flag to denote if the column is required or not.

    This is an internal cache.  Use column.is_required instead.
    """
    _is_required = False

    """
    The list of allowed search operators for this column.

    All the various search methods reference this list.  The idea is that a column can just fill out this list
    instead of having to override all the methods.
    """
    _allowed_search_operators = ["<=>", "!=", "<=", ">=", ">", "<", "=", "in", "is not null", "is null", "like"]

    """
    The class to use when documenting this column
    """
    auto_doc_class: Type[AutoDocSchema] = AutoDocString

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        default: str | None = None,
        setable: str | Callable[..., str] | None = None,
        is_readable: bool = True,
        is_writeable: bool = True,
        is_searchable: bool = True,
        is_temporary: bool = False,
        validators: clearskies.typing.validator | list[clearskies.typing.validator] = [],
        on_change_pre_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_post_save: clearskies.typing.action | list[clearskies.typing.action] = [],
        on_change_save_finished: clearskies.typing.action | list[clearskies.typing.action] = [],
        created_by_source_type: str = "",
        created_by_source_key: str = "",
        created_by_source_strict: bool = True,
    ):
        pass

    def get_model_columns(self):
        """ Return the columns or the model this column is attached to. """
        return self.model_class.get_columns()

    def finalize_configuration(self, model_class: type, name: str) -> None:
        """
        Finalize and check the configuration.

        This is an external trigger called by the model class when the model class is ready.
        The reason it exists here instead of in the constructor is because some columns are tightly
        connected to the model class, and can't validate configuration until they know what the model is.
        Therefore, we need the model involved, and the only way for a property to know what class it is
        in is if the parent class checks in (which is what happens here).
        """
        self.model_class = model_class
        self.name = name
        self.finalize_and_validate_configuration()

    def from_backend(self, value):
        """
        Takes the backend representation and returns a python representation

        For instance, for an SQL date field, this will return a Python DateTime object
        """
        return str(value)

    def to_backend(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Makes any changes needed to save the data to the backend.

        This typically means formatting changes - converting DateTime objects to database
        date strings, etc...
        """
        if self.name not in data:
            return data

        return {**data, self.name: str(data[self.name])}

    @overload
    def __get__(self, instance: None, cls: type) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: type):
        pass

    def __get__(self, instance: Model, cls: type):
        if instance is None:
            # Normally this gets filled in when the model is initialized.  However, the condition builders (self.equals, etc...)
            # can be called from the class directly, before the model is initialized and everything is populated.  This
            # can cause trouble, but by filling in the model class we can give enough information for them to get the
            # job done.  They have a special flow for this, we just have to provide the model class (and the __get__
            # function is always called, so this fixes it).
            self.model_class = cls
            return self

        if self.name not in instance._data:
            return None # type: ignore

        if self.name not in instance._transformed_data:
            instance._transformed_data[self.name] = self.from_backend(instance._data[self.name])

        return instance._transformed_data[self.name]

    def __set__(self, instance: Model, value) -> None:
        instance._next_data[self.name] = value

    def finalize_and_validate_configuration(self):
        super().finalize_and_validate_configuration()

        if self.setable is not None and self.created_by_source_type:
            raise ValueError(
                "You attempted to set both 'setable' and 'created_by_source_type', but these configurations are mutually exclusive.  You can only set one for a given column"
            )

        if (self.created_by_source_type and not self.created_by_source_key) or (
            not self.created_by_source_type and self.created_by_source_key
        ):
            raise ValueError(
                "You only set one of 'created_by_source_type' and 'created_by_source_key'.  You have to either set both of them (which enables the 'created_by' feature of the column) or you must set neither of them."
            )

    @property
    def is_unique(self) -> bool:
        """
        Return True/False to denote if this column should always have unique values
        """
        if self._is_unique is None:
            self._is_unique = any([validator.is_unique for validator in self.validators])
        return self._is_unique

    @property
    def is_required(self):
        """
        Return True/False to denote if this column should is required
        """
        if self._is_required is None:
            self._is_required = any([validator.is_required for validator in self.validators])
        return self._is_required

    def additional_write_columns(self, is_create=False) -> dict[str, Self]:
        """
        Returns any additional columns that should be included in write operations.

        Some column types, and some validation requirements, necessitate the presence of additional
        columns in the save operation.  This function adds those in so they can be included in the
        API call.
        """
        additional_write_columns: dict[str, Self] = {}
        for validator in self.validators:
            if not isinstance(validator, Validator):
                continue
            additional_write_columns = {
                **additional_write_columns,
                **validator.additional_write_columns(is_create=is_create),
            }
        return additional_write_columns

    def to_json(self, model: clearskies.model.Model) -> dict[str, Any]:
        """
        Grabs the column out of the model and converts it into a representation that can be turned into JSON
        """
        return {self.name: self.__get__(model, model.__class__)}

    def input_errors(self, model: clearskies.model.Model, data: dict[str, Any]) -> dict[str, Any]:
        """
        Check the given dictionary of data for any possible input errors.

        This accepts all the data being saved, and not just the value for this column.  The reason is because
        some input valdiation flows require more than one piece of data.  For instance, a user may be asked
        to type a specific piece of input more than once to minimize the chance of typos, or a user may
        have to provide their password when changing security-related columns.

        This also returns a dictionary, rather than an error message, so that a column can also return an error
        message for more than one column at a time if needed.

        If there are no input errors then this should simply return an empty dictionary.

        This method calls `self.input_error_for_value` and then also calls all the validators attached to the
        column so, if you're building your own column and have some specific input validation you need to do,
        you probably want to extend `input_error_for_value` as that is the one intended checks for a column type.

        Note: this is not called when you directly invoke the `save`/`create` method of a model.  This is only
        used by handlers when processing user input (e.g. API calls).
        """
        if self.name in data and data[self.name]:
            error = self.input_error_for_value(data[self.name])
            if  error:
                return {self.name: error}

        for validator in self.validators:
            if hasattr(validator, "injectable_properties"):
                validator.injectable_properties(self.di)

            error = validator(model, self.name, data)
            if error:
                return {self.name: error}

        return {}

    def check_search_value(
        self,
        value: str,
        operator: str | None=None,
        relationship_reference: str | None=None
    ) -> str:
        """
        This is called by the search operation in the various API-related handlers to validate a search value.

        Generally, this just defers to self.input_error_for_value, but it is a separate method in case you
        need to change your input validation logic specifically when checking a search value.
        """
        return self.input_error_for_value(value, operator=operator)

    def input_error_for_value(self, value: str, operator: str | None=None) -> str:
        """
        Check if the given value is an allowed value.

        This method is intended for checks that are specific to the column type (e.g. this is where an
        email column checks that the value is an actual email, or a datetime column checks for a valid
        datetime).  The `input_errors` method does a bit more, so in general it's easier to extend this one.

        This method is passed in the value to check.  It should return a string.  If the data is valid,
        then return an empty string.  Otherwise return a human-readable error message.

        At times an operator will be passed in.  This is used when the user is searching instead of saving.
        In this case, the check can vary depending on the operator.  For instance, if it's a wildcard search
        then an email field only has to verify the type is a string (since the user may have only entered
        the beginning of an email address), but if it's an exact search then you would expect the value to be
        an actual email.

        Note: this is not called when you directly invoke the `save`/`create` method of a model.  This is only
        used by handlers when processing user input (e.g. API calls).
        """
        return ""

    def pre_save(self, data: dict[str, Any], model: clearskies.model.Model) -> dict[str, Any]:
        """
        Make any necessary changes to the data before starting the save process

        The difference between this and to_backend is that to_backend only affects
        the data as it is going into the database, while this affects the data that will get persisted
        in the object as well.  So for instance, for a "created" field, pre_save may fill in the current
        date with a Python DateTime object when the record is being saved, and then to_backend may
        turn that into an SQL-compatible date string.

        Note: this is called during the `pre_save` step in the lifecycle of the save process.  See the
        model class for more details.
        """
        if not model and self.created_by_source_type:
                data[self.name] = self._extract_value_from_source_type()
        if self.setable:
            if callable(self.setable):
                input_output = self.di.build("input_output", cache=True)
                data[self.name] = self.di.call_function(self.setable, data=data, model=model, **input_output.get_context_for_callables())
            else:
                data[self.name] = self.setable
        if not model and self.default and self.name not in data:
            data[self.name] = self.default
        if self.on_change_pre_save and model.is_changing(self.name, data):
            data = self.execute_actions_with_data(self.on_change_pre_save, model, data)
        return data

    def post_save(self, data: dict[str, Any], model: clearskies.model.Model, id: int | str) -> None:
        """
        Make any changes needed after persisting data to the backend.

        This lives in the `post_save` hook of the save lifecycle.  See the model class for more details.
        `data` is the data dictionary being saved.  `model` is obviously the model object that initiated the
        save.

        This happens after the backend is updated but before the model is updated.  Therefore, You can tell the
        difference between a create operation and an update operation by checking if the model exists: `if model`.
        For a create operation, the model will be empty (it evaluates to False).  The opposite is true for an update
        operation.

        Any return value will be ignored.  If you need to make additional changes in the backend, you
        have to execute a new save operation.
        """
        if self.on_change_post_save and model.is_changing(self.name, data):
            self.execute_actions_with_data(self.on_change_post_save, model, data, context="on_change_post_save")

    def save_finished(self, model: clearskies.model.Model) -> None:
        """
        Make any necessary changes needed after a save has completely finished.

        This is typically used for actions set by the developer.   Column-specific behavior usually lives in
        `pre_save` or `post_save`.  See the model class for more details about the various lifecycle hooks during
        a save.
        """
        if self.on_change_save_finished and model.was_changed(self.name):
            self.execute_actions(self.on_change_save_finished, model)

    def pre_delete(self, model):
        """
        Make any changes needed to the data before starting the delete process
        """
        pass

    def post_delete(self, model):
        """
        Make any changes needed to the data before finishing the delete process
        """
        pass

    def _extract_value_from_source_type(self) -> Any:
        """
        For columns with `created_by_source_type` set, this fetches the appropriate value from the request
        """
        input_output = self.di.build("input_output", cache=True)
        source_type = self.created_by_source_type
        if source_type == "authorization_data":
            data = input_output.get_authorization_data()
        elif source_type == "http_header":
            data = input_output.get_request_headers()
        elif source_type == "routing_data":
            data = input_output.get_routing_data()

        if self.created_by_source_key not in data and self.created_by_source_strict:
            raise ValueError(
                f"Column '{self.name}' is configured to load the key named '{self.created_by_source_key}' from " +
                f"the {self.created_by_source_type}', but this key was not present in the request."
            )

        return data.get(self.created_by_source_key, "N/A")

    def execute_actions_with_data(
        self,
        actions: list[clearskies.typing.action],
        model: clearskies.model.Model,
        data: dict[str, Any],
        context: str = "on_change_pre_save",
    ) -> dict[str, Any]:
        """
        Executes a given set of actions and expects data to be both provided and returned
        """
        input_output = self.di.build("input_output", cache=True)
        for (index, action) in enumerate(actions):
            new_data = self.di.call_function(
                action,
                model=model,
                data=data,
                **input_output.get_context_for_callables(),
            )
            if not isinstance(new_data, dict):
                raise ValueError(f"Return error for action #{index+1} in 'on_change_pre_save' for column '{self.name}' in model '{self.model_class.__name__}': this action must return a dictionary but returned an object of type '{new_data.__class__.__name__}' instead")
            data = {
                **data,
                **new_data,
            }
        return data

    def execute_actions(
        self,
        actions: list[clearskies.typing.action],
        model: clearskies.model.Model,
    ) -> None:
        """
        Executes a given set of actions
        """
        input_output = self.di.build("input_output", cache=True)
        for action in actions:
            self.di.call_function(action, model=model, **input_output.get_context_for_callables())

    def values_match(self, value_1, value_2):
        """
        Compares two values to see if they are the same.

        This is mainly used to compare incoming data with old data to determine if a column has changed.

        Note that these checks shouldn't make any assumptions about whether or not data has gone through the
        to_backend/from_backend functions.  For instance, a datetime field may find one value has a date
        that is formatted as a string, and the other as a DateTime object.  Plan appropriately.
        """
        return value_1 == value_2

    def add_search(
        self,
        model: clearskies.model.Model,
        value: str,
        operator: str="",
        relationship_reference: str=""
    ) -> clearskies.model.Model:
        return model.where(self.build_condition(value, operator=operator))

    def build_condition(
        self,
        value: str,
        operator: str="",
        column_prefix: str=""
    ):
        """
        This is called by the read (and related) handlers to turn user input into a condition.

        Note that this may look like it is vulnerable to SQLi, but it isn't.  These conditions aren't passed directly
        into a query.  Rather, they are parsed by the condition parser before being sent into the backend.
        The condition parser can safely reconstruct the original pieces, and the backend can then use the data
        safely (and remember, the backend may not be an SQL anyway)

        As a result, this is perfectly safe for any user input, assuming normal system flow.
        """
        if not operator:
            operator = "="
        if operator.lower() == "like":
            return f"{column_prefix}{self.name} LIKE '%{value}%'"
        return f"{column_prefix}{self.name}{operator}{value}"

    def is_allowed_operator(
        self,
        operator: str,
        relationship_reference: str="",
    ):
        """
        This is called when processing user data to decide if the end-user is specifying an allowed operator
        """
        return operator.lower() in self._allowed_search_operators

    def n_plus_one_add_joins(self, model: clearskies.model.Model, column_names: list[str] = []) -> clearskies.model.Model:
        """
        Add any additional joins to solve the N+1 problem.
        """
        return model

    def n_plus_one_join_table_alias_prefix(self):
        """
        A table alias to use with joins for n+1 solutions.

        When joining tables in for n+1 solutions, you can't just do a SELECT * on the new table, because that
        often results in duplicate column names.  A solution that generally works across the board is to select
        specific columns from the joined table and alias them, adding a common prefix.  Then, the data from the
        joined table can be reconstructed automatically by finding all columns with that prefix (and then removing
        the prefix).  This function returns that prefix for that alias.

        Now, technically this isn't function isn't used at all by the base class, so this definition is fairly
        pointless.  It isn't marked as an abstract method because most model columns don't need it either.
        Rather, this function is here mostly for documentation so it's easier to understand how to implement
        support for n+1 solutions when needed.  See the belongs_to column for a full implementation reference.
        """
        return "join_table_" + self.name

    def add_join(self, model: Model) -> Model:
        return model

    def where_for_request(
        self,
        model: clearskies.model.Model,
        routing_data: dict[str, str],
        authorization_data: dict[str, Any],
        input_output
    ) -> clearskies.model.Model:
        """
        A hook to automatically apply filtering whenever the column makes an appearance in a get/update/list/search handler.

        This hook is called by all the handlers that execute queries, so if your column needs to automatically
        do some filtering whenever the model shows up in an API endpoint, this is the place for it.
        """
        return model

    def name_for_building_condition(self) -> str:
        if self._config and "name" in self._config:
            return self.name

        if not self._config or not self._config.get("model_class"):
            raise ValueError(f"A condition builder was called but the model class isn't set.  This means that the __get__ method for column class {self.__class__.__name__} forgot to set `self.model_class = cls`")

        for attribute_name in dir(self.model_class):
            if id(getattr(self.model_class, attribute_name)) != id(self):
                continue
            self.name = attribute_name
            break

        return self.name

    def equals(self, value) -> Condition:
        name = self.name_for_building_condition()
        if "=" not in self._allowed_search_operators:
            raise ValueError(f"An 'equals search' is not allowed for '{self.model_class.__name__}.{name}'.")
        value = self.to_backend({name: value}).get(name)
        return ParsedCondition(name, '=', [value])

    def spaceship(self, value) -> Condition:
        name = self.name_for_building_condition()
        if "<=>" not in self._allowed_search_operators:
            raise ValueError(f"A 'spaceship' search is not allowed for '{self.model_class.__name__}.{name}'.")
        value = self.to_backend({name: value}).get(name)
        return ParsedCondition(name, '<=>', [value])

    def not_equals(self, value) -> Condition:
        name = self.name_for_building_condition()
        if "!=" not in self._allowed_search_operators:
            raise ValueError(f"A 'not equals' search is not allowed for '{self.model_class.__name__}.{name}'.")
        value = self.to_backend({name: value}).get(name)
        return ParsedCondition(name, '!=', [value])

    def less_than_equals(self, value) -> Condition:
        name = self.name_for_building_condition()
        if "<=" not in self._allowed_search_operators:
            raise ValueError(f"A 'less than or equals' search is not allowed for '{self.model_class.__name__}.{name}'.")
        value = self.to_backend({name: value}).get(name)
        return ParsedCondition(name, '<=', [value])

    def greater_than_equals(self, value) -> Condition:
        name = self.name_for_building_condition()
        if ">=" not in self._allowed_search_operators:
            raise ValueError(f"A 'greater than' or equals search is not allowed for '{self.model_class.__name__}.{name}'.")
        value = self.to_backend({name: value}).get(name)
        return ParsedCondition(name, '>=', [value])

    def less_than(self, value) -> Condition:
        name = self.name_for_building_condition()
        if "<" not in self._allowed_search_operators:
            raise ValueError(f"A 'less than' search is not allowed for '{self.model_class.__name__}.{name}'.")
        value = self.to_backend({name: value}).get(name)
        return ParsedCondition(name, '<', [value])

    def greater_than(self, value) -> Condition:
        name = self.name_for_building_condition()
        if ">" not in self._allowed_search_operators:
            raise ValueError(f"A 'greater than' search is not allowed for '{self.model_class.__name__}.{name}'.")
        value = self.to_backend({name: value}).get(name)
        return ParsedCondition(name, '>', [value])

    def is_in(self, values) -> Condition:
        name = self.name_for_building_condition()
        if "in" not in self._allowed_search_operators:
            raise ValueError(f"An 'in' search is not allowed for '{self.model_class.__name__}.{name}'.")
        if not isinstance(values, list):
            raise TypeError("You must pass a list in to column.is_in")
        final_values = []
        for value in values:
            final_values.append(self.to_backend({name: value}).get(name))
        return ParsedCondition(name, 'in', final_values)

    def is_not_null(self) -> Condition:
        name = self.name_for_building_condition()
        if "is not null" not in self._allowed_search_operators:
            raise ValueError(f"An 'is not null' search is not allowed for '{self.model_class.__name__}.{name}'.")
        return ParsedCondition(name, 'is not null', [])

    def is_null(self) -> Condition:
        name = self.name_for_building_condition()
        if "is null" not in self._allowed_search_operators:
            raise ValueError(f"An 'is null' search is not allowed for '{self.model_class.__name__}.{name}'.")
        return ParsedCondition(name, 'is null', [])

    def like(self, value) -> Condition:
        name = self.name_for_building_condition()
        if "like" not in self._allowed_search_operators:
            raise ValueError(f"A 'like' search is not allowed for '{self.model_class.__name__}.{name}'.")
        value = self.to_backend({name: value}).get(name)
        return ParsedCondition(name, 'like', [value])

    def documentation(self, name=None, example=None, value=None) -> list[AutoDocSchema]:
        return [self.auto_doc_class(name if name is not None else self.name, example=example, value=value)]
