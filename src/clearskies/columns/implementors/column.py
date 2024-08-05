from abc import ABC
import re
from .. import binding_config
import inspect


class Column(ABC):
    _auto_doc_class = AutoDocString

    def __init__(self, di):
        self.di = di

    def configure(self, name, configuration, model_class):
        if not name:
            raise ValueError(f"Missing name for column in '{model_class.__name__}'")
        self.model_class = model_class
        self.name = name
        self._check_configuration(configuration)
        configuration = self._finalize_configuration(configuration)
        self.configuration = configuration

    def additional_write_columns(self, is_create=False):
        additional_write_columns = {}
        for requirement in self.config("input_requirements"):
            additional_write_columns = {
                **additional_write_columns,
                **requirement.additional_write_columns(is_create=is_create),
            }
        return additional_write_columns

    def from_backend(self, value):
        """
        Takes the database representation and returns a python representation

        For instance, for an SQL date field, this will return a Python DateTime object
        """
        return value

    def to_backend(self, data):
        """
        Makes any changes needed to save the data to the backend.

        This typically means formatting changes - converting DateTime objects to database
        date strings, etc...
        """
        return data

    def to_json(self, model):
        """
        Grabs the column out of the model and converts it into a representation that can be turned into JSON
        """
        return {self.name: model.get(self.name, silent=True)}

    def input_errors(self, model, data):
        error = self.check_input(model, data)
        if error:
            return {self.name: error}

        for requirement in self.config("input_requirements"):
            error = requirement.check(model, data)
            if error:
                return {self.name: error}

        return {}

    def check_input(self, model, data):
        if self.name not in data or not data[self.name]:
            return ""
        return self.input_error_for_value(data[self.name])

    def pre_save(self, data, model):
        """
        Make any changes needed to the data before starting the save process

        The difference between this and transform_for_database is that transform_for_database only affects
        the data as it is going into the database, while this affects the data that will get persisted
        in the object as well.  So for instance, for a "created" field, pre_save may fill in the current
        date with a Python DateTime object when the record is being saved, and then transform_for_database may
        turn that into an SQL-compatible date string.

        The difference between this and post_save is that this happens before the database is updated.
        As a result, if you need the model id to make your changes, it has to happen in post_save, not pre_save
        """
        if not model.exists:
            source_type = self.configuration.get("created_by_source_type")
            if source_type:
                if source_type == "authorization_data":
                    authorization_data = self.di.build("input_output", cache=True).get_authorization_data()
                    data[self.name] = authorization_data.get(self.config("created_by_source_key"), "N/A")
        if "setable" in self.configuration:
            setable = self.configuration["setable"]
            if callable(setable):
                data[self.name] = self.di.call_function(setable, data=data, model=model)
            else:
                data[self.name] = setable
        if not model.exists and "default" in self.configuration and self.name not in data:
            data[self.name] = self.configuration["default"]
        return data

    def post_save(self, data, model, id):
        """
        Make any changes needed after saving to the database

        data is the data being saved and id is the id of the record.   Note that while the database is updated
        before this is called, the model isn't, so there will be a difference between what is in the database
        and what is in the object.
        """
        return data

    def save_finished(self, model):
        """
        Make any necessary changes needed after a save has completely finished.

        This is typically used for configurable triggers set by the developer.   Column-specific behavior
        that needs to always happen is placed in pre_save or post_save because those affect the save
        process itself.
        """
        on_change_actions = self.config("on_change", silent=True)
        if on_change_actions and model.was_changed(self.name):
            self.execute_actions(on_change_actions, model)

    def values_match(self, value_1, value_2):
        """
        Compares two values to see if they are the same
        """
        return value_1 == value_2

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

    def can_provide(self, column_name):
        """
        This works together with self.provide to load ancillary data

        For instance, a foreign key will have an "id" column such as `user_id` but it can also load up
        the user model, which you expect to happen by requesting `model.user`.  If a model receives a
        request for a column name that it doesn't recognize, it will loop through all the columns and
        call `can_provide` with the column name.  We then have to return True or False to denote whether
        or not we can provide the thing being requested.  If we return True then the model will then
        call `column.provide` with the data from the model and the requested column name
        """
        return False

    def provide(self, data, column_name):
        """
        This is called if the column declares that it can provide something, and should return the value

        See can_provide for more details on the flow here
        """
        pass

    def execute_actions(self, actions, model):
        for action in actions:
            if type(action) == binding_config.BindingConfig:
                action = self.di.build(action)
            elif inspect.isclass(action):
                action = self.di.build(action)
            if hasattr(action, "__call__"):
                self.di.call_function(action.__call__, model=model)
            else:
                self.di.call_function(action.__call__, model=model)

    def add_search(self, models, value, operator=None, relationship_reference=None):
        return models.where(self.build_condition(value, operator=operator))

    def build_condition(self, value, operator=None, column_prefix=""):
        """
        This is called by the read (and related) handlers to turn user input into a condition.

        Note that this may look like it is vulnerable to SQLi, but it isn't.  These conditions aren't passed directly
        into a query.  Rather, they are parsed by the condition parser before being sent into the backend.
        The condition parser can safely reconstruct the original pieces, and the backend can then use the data
        safely (and remember, the backend may not be an SQL anyway)

        As a result, this is perfectly safe for any user input, assuming normal system flow.
        """
        return f"{column_prefix}{self.name}={value}"

    def is_allowed_operator(self, operator, relationship_reference=None):
        """
        This is called when processing user data to decide if the end-user is specifying an allowed operator
        """
        return operator == "="

    def configure_n_plus_one(self, models):
        return models

    def check_search_value(self, value, operator=None, relationship_reference=None):
        return self.input_error_for_value(value, operator=operator)

    def input_error_for_value(self, value, operator=None):
        return ""

    def where_for_request(self, models, routing_data, authorization_data, input_output):
        """
        A hook to automatically apply filtering whenever the column makes an appearance in a get/update/list/search handler.
        """
        return models

    def documentation(self, name=None, example=None, value=None):
        return self._auto_doc_class(name if name is not None else self.name, example=example, value=value)
