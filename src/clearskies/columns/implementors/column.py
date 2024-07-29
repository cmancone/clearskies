from abc import ABC
import re
from ..autodoc.schema import String as AutoDocString
from .. import input_requirements
from .. import binding_config
import inspect


class Column(ABC):
    _auto_doc_class = AutoDocString
    _is_unique = None
    _is_required = None
    configuration = None
    common_configs = [
        "input_requirements",
        "class",
        "is_writeable",
        "is_temporary",
        "on_change",
        "default",
        "setable",
        "created_by_source_type",
        "created_by_source_key",
    ]

    def __init__(self, di):
        self.di = di

    my_configs = []
    required_configs = []

    @property
    def is_writeable(self):
        is_writeable = self.config("is_writeable", True)
        return True if (is_writeable or is_writeable is None) else False

    @property
    def is_readable(self):
        return True

    @property
    def is_unique(self):
        if self._is_unique is None:
            requirements = self.config("input_requirements")
            self._is_unique = False
            for requirement in requirements:
                if isinstance(requirement, input_requirements.Unique):
                    self._is_unique = True
        return self._is_unique

    @property
    def is_temporary(self):
        return bool(self.config("is_temporary", silent=True))

    @property
    def is_required(self):
        if self._is_required is None:
            requirements = self.config("input_requirements")
            self._is_required = False
            for requirement in requirements:
                if isinstance(requirement, input_requirements.Required):
                    self._is_required = True
        return self._is_required

    def model_column_configurations(self):
        nargs = len(inspect.getfullargspec(self.model_class.__init__).args) - 1
        fake_model = self.model_class(*([""] * nargs))
        return fake_model.all_columns()

    def configure(self, name, configuration, model_class):
        if not name:
            raise ValueError(f"Missing name for column in '{model_class.__name__}'")
        self.model_class = model_class
        self.name = name
        self._check_configuration(configuration)
        configuration = self._finalize_configuration(configuration)
        self.configuration = configuration

    def _check_configuration(self, configuration):
        """Check the configuration and throw exceptions as needed"""
        for key in self.required_configs:
            if key not in configuration:
                raise KeyError(
                    f"Missing required configuration '{key}' for column '{self.name}' in '{self.model_class.__name__}'"
                )
        for key in configuration.keys():
            if key not in self.common_configs and key not in self.my_configs and key not in self.required_configs:
                raise KeyError(
                    f"Configuration '{key}' not allowed for column '{self.name}' in '{self.model_class.__name__}'"
                )
        if "is_writeable" in configuration and type(configuration["is_writeable"]) != bool:
            raise ValueError("'is_writeable' must be a boolean")
        if configuration.get("on_change"):
            self._check_actions(configuration.get("on_change"), "on_change")

        self._check_created_by_source(configuration)

    def _finalize_configuration(self, configuration):
        """Make any changes to the configuration/fill in defaults"""
        if not "input_requirements" in configuration:
            configuration["input_requirements"] = []
        return configuration

    def _check_created_by_source(self, configuration):
        source_type = configuration.get("created_by_source_type")
        source_key = configuration.get("created_by_source_key")
        if not source_type and not source_key:
            return

        error_prefix = f"Misconfiguration for column '{self.name}' in '{self.model_class.__name__}': "
        if not source_type or not source_key:
            raise ValueError(
                f"{error_prefix} must provide both 'created_by_source_type' and 'created_by_source_key' but only one was provided."
            )

        if not isinstance(source_type, str):
            raise ValueError(
                f"{error_prefix} 'created_by_source_type' must be a string but is a '"
                + source_type.__class__.__name__
                + "'"
            )
        if not isinstance(source_key, str):
            raise ValueError(
                f"{error_prefix} 'created_by_source_key' must be a string but is a '"
                + source_key.__class__.__name__
                + "'"
            )

        allowed_types = ["authorization_data"]
        if source_type not in allowed_types:
            raise ValueError(
                f"{error_prefix} 'created_by_source_type' must be one of '" + "', '".join(allowed_types) + "'"
            )
        if configuration.get("setable"):
            raise ValueError(f"{error_prefix} you cannot set both 'setable' and 'created_by_source_type'")

    def _check_actions(self, actions, trigger_name):
        """Check that the given actions are actually understandable by the system"""
        if type(actions) != list:
            raise ValueError(
                "The actions provided to a trigger should be a list of callables/binding configs, but something "
                + f"else was provided for the '{trigger_name}' trigger in '{self.model_class.__name__}'"
            )
        for index, action in enumerate(actions):
            # if it's callable we're good.  This includes functions, lambdas, callable objects,
            # and classes that will be callable when instantiated
            if callable(action):
                continue
            # the above pretty much covers everything.  The only thing that we support otherwise
            # is a binding config containing a callable class.
            if type(action) == binding_config.BindingConfig:
                if callable(action.object_class):
                    continue

            raise ValueError(
                f"Invalid action: action #{index+1} for trigger '{trigger_name} in '{self.model_class.__name__}'"
            )

    def config(self, key, silent=False):
        if not key in self.configuration:
            if silent:
                return None
            raise KeyError(f"column '{self.__class__.__name__}' does not have a configuration named '{key}'")

        return self.configuration[key]

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

    def validate_models_class(self, models_class, config_name="parent_models_class"):
        if not hasattr(models_class, "model_class"):
            if hasattr(models_class, "columns_configuration"):
                raise ValueError(
                    f"'{config_name}' in configuration for column '{self.name}' in model class "
                    + f"'{self.model_class.__name__}' appears to be a Model class, but it should be a Models class"
                )
            else:
                raise ValueError(
                    f"'{config_name}' in configuration for column '{self.name}' should be a Models class, "
                    + f"but it appears to be something unknown."
                )

    def camel_to_nice(self, string):
        string = re.sub("(.)([A-Z][a-z]+)", r"\1 \2", string)
        string = re.sub("([a-z0-9])([A-Z])", r"\1 \2", string).lower()
        return string

    def documentation(self, name=None, example=None, value=None):
        return self._auto_doc_class(name if name is not None else self.name, example=example, value=value)
