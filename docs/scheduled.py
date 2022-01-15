import clearskies
import datetime
class Scheduled(clearskies.column_types.DateTime):
    # if we specify some config names here, the base `_check_configuration` method will
    # raise exceptions if the developer doesn't set them.
    required_configs = [
        'source_column_name',
        'timedelta',
    ]

    @property
    def is_writeable(self):
        return False

    def _check_configuration(self, configuration):
        # This will automatically check for our required configs
        super()._check_configuration(configuration)

        # but we have to check the values.  In particular, the `source_column_name` should correspond
        # to an actual column in our model.  We check this via the model column configuration, which is a dictionary
        # containing all the known columns in the model (e.g., the result of calling model.columns_configuration(),
        # plus the id field.
        model_columns = self.model_column_configurations()
        if configuration['source_column_name'] not in model_columns:
            raise KeyError(
                f"Column '{self.name}' references source column {configuration['source_column_name']} but this " + \
                "column does not exist in model '{self.model_class.__name__}'"
            )

        # now let's verify that the contents of timedelta is a valid set of arguments for the timedelta object
        # first, make sure it is a dictionary
        if type(configuration['timedelta']) != dict:
            raise ValueError(
                f"timedelta for column '{self.name}' in model class {self.model_class.__name__} should be a " + \
                "dictionary with a valid set of datetime.timedelta parameters, but it is not a dictionary"
            )
        # then just pass it to datetime.timedelta and see if it works.  This doesn't give us a great error
        # message, but it's something
        try:
            datetime.timedelta(**configuration['timedelta'])
        except Exception:
            raise ValueError(
                "Invalid timedelta configuration passed for column '{self.name}' in model class " + \
                "'{self.model_class.__name__}'.  See datetime.timedelta documentation for allowed config keys"
            )

    def pre_save(self, data, model):
        source_column_name = self.config('source_column_name')
        if source_column_name not in data:
            return data

        return {
        # always return the previous data first
            **data,

        # and then add on any new data
            self.name:
            data[source_column_name] + datetime.timedelta(**self.config('timedelta'))
        }
def scheduled(name, **kwargs):
    return clearskies.column_types.build_column_config(name, Scheduled, **kwargs)
