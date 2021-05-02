from abc import ABC


class Column(ABC):
    configuration = None
    common_configs = [
        'input_requirements',
        'class',
        'is_writeable',
    ]
    my_configs = []
    required_configs = []

    @property
    def is_writeable(self):
        is_writeable = self.config('is_writeable', True)
        return True if (is_writeable or is_writeable is None) else False

    @property
    def is_readable(self):
        return True

    def configure(self, name, configuration, model_class):
        if not name:
            raise ValueError(f"Missing name for column in '{model_class.__name__}'")
        self.model_class = model_class
        self.name = name
        self._check_configuration(configuration)
        configuration = self._finalize_configuration(configuration)
        self.configuration = configuration

    def _check_configuration(self, configuration):
        """ Check the configuration and throw exceptions as needed """
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
        if 'is_writeable' in configuration and type(configuration['is_writeable']) != bool:
            raise ValueError("'is_writeable' must be a boolean")

    def _finalize_configuration(self, configuration):
        """ Make any changes to the configuration/fill in defaults """
        if not 'input_requirements' in configuration:
            configuration['input_requirements'] = []
        return configuration

    def config(self, key, silent=False):
        if not key in self.configuration:
            if silent:
                return None
            raise KeyError(
                f"column '{self.__class__.__name__}' does not have a configuration named '{key}'"
            )

        return self.configuration[key]

    def from_database(self, value):
        """
        Takes the database representation and returns a python representation

        For instance, for an SQL date field, this will return a Python DateTime object
        """
        return value

    def to_database(self, data):
        """
        Makes any changes needed to save the data to the database.

        This typically means formatting changes - converting DateTime objects to database
        date strings, etc...
        """
        return data

    def to_json(self, model):
        """
        Grabs the column out of the model and converts it into a representation that can be turned into JSON
        """
        return model.__getattr__(self.name)

    def input_errors(self, model, data):
        error = self.check_input(model, data)
        if error:
            return {self.name: error}

        for requirement in self.config('input_requirements'):
            error = requirement.check(model, data)
            if error:
                return {self.name: error}

        return {}

    def check_input(self, model, data):
        if not self.name in data or not data[self.name]:
            return ''
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
        return data

    def post_save(self, data, model, id):
        """
        Make any changes needed after saving to the database

        data is the data being saved and id is the id of the record.   Note that while the database is updated
        before this is called, the model isn't, so there will be a difference between what is in the database
        and what is in the object.
        """
        return data

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

    def build_condition(self, value, operator=None):
        """
        This is called by the read (and related) handlers to turn user input into a condition.

        Note that this may look like it is vulnerable to SQLi, but it isn't.  These conditions aren't passed directly
        into a query.  Rather, they are parsed by the condition parser before being sent into the backend.
        The condition parser can safely reconstruct the original piecesk, and the backend can then use the data
        safely (and remember, the backend may not be an SQL anyway)

        As a result, this is perfectly safe for any user input, assuming normal system flow.
        """
        return f"{self.name}={value}"

    def is_allowed_operator(self, operator):
        """
        This is called when processing user data to decide if the end-user is specifying an allowed operator
        """
        return operator == '='

    def check_search_value(self, value):
        return self.input_error_for_value(value)

    def input_error_for_value(self, value):
        return ''
