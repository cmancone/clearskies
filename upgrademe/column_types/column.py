from abc import ABC


class Column(ABC):
    def configure(self, name, configuration, model_class):
        if not name:
            raise ValueError(f"Missing name for column in '{model_class.__name__}'")
        self.model_class = model_class
        self.name = name
        self._validate_configuration(configuration)
        self.configuration = self._finalize_configuration(configuration)

    def _validate_configuration(self, configuration):
        """ Check the configuration and throw exceptions as needed """
        pass

    def _finalize_configuration(self, configuration):
        """ Make any changes to the configuration/fill in defaults """
        return configuration

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

    def pre_save(self, data):
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

    def post_save(self, data, id):
        """
        Make any changes needed after saving to the database

        data is the data being saved and id is the id of the record.   Note that while the database is updated
        before this is called, the model isn't, so there will be a difference between what is in the database
        and what is in the object.
        """
        return data

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
