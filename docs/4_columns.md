# Columns

Columns are a first class citizen in clearskies, and the preferred avenue for making business logic reusable.  Like in other frameworks, columns are attached to models to define its schema.  Clearskies uses this schema to automatically generate API endpoints, validate user input, etc...

clearskies comes with a number of pre-defined column types to cover "standard" framework usage, relationships, etc.  These are all meant to be extended, which is what you want to do to add your own business logic.  In an ideal world of course, you won't have to do this _too_ often.

1. [Basic Usage](#basic-usage)
2. [Input Requirements](#input-requirements)
3. [Life Cycle](#life-cycle)
4. [Custom Column Types](#custom-column-types)

## Basic Usage

Columns are used to build the schema in a model via the `columns_configuration` method like so:

```
from collections import OrderedDict
from clearskies import Model
from clearskies.column_types import string, email, integer, created, updated


class User(Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            string('name'),
            email('email'),
            integer('age'),
            created('created'),
            updated('updated'),
        ])
```

`columns_configuration` returns an ordered dictionary: the key is the name of the column and the value is the column configuration.  The functions exported from the `column_types` [module](../src/clearskies/column_types/__init__.py) (e.g. `string`, `email`, `integer`, etc...) just simplify the construction of this dictionary.  They accept the name of the column and then any additional configuration settings.  All column types have some standard configuration options, and some have additional configuration options, some of which may be required.  All column types have the following configuration options:

| Name               | Type  | Default | Description                                                                                    |
|--------------------|-------|---------|------------------------------------------------------------------------------------------------|
| input_requirements | array | []      | List of input requirements for the column                                                      |
| is_writeable       | bool  | True    | Whether or not the column is writeable by default                                              |
| is_temporary       | bool  | False   | Whether or not it is a temporary column - temporary columns are never persisted to the backend |

These are the currently supported column types (the names correspond to the function exported from the `column_types` module which you can use to inject it into a model schema).

| Name         | Description                                                                   |
|--------------|-------------------------------------------------------------------------------|
| belongs_to   | A standard belongs to relationship connecting child records to parents        |
| created      | Automatically records the timestamp when a model is created                   |
| datetime     | A date time column                                                            |
| email        | For email addresses                                                           |
| float        | For floating point numbers                                                    |
| has_many     | A standard "has many" relationship connecting a parent to child records       |
| integer      | For integers                                                                  |
| json         | For storing and retrieving structured data via JSON                           |
| many_to_many | A standard has many relationship that uses a mapping table to connect records |
| select       | A pre-defined list of selectable options (e.g. an ENUM field)                 |
| string       | Generic string type                                                           |
| updated      | Automatically records the timestamp when a model is updated                   |

## Input Requirements

All column types comes with the necessary validation rules to validate their "type" of data: a column with the `integer` column type will not allow non-integer data, the `email` column type will check for a valid email address, the `belongs_to` column type will ensure that the selected record actually exists, etc...  Additional input requirements can be attached to columns as needed.  Similar to with columns, there are a series of functions that are exported by the [input_requirements module](../src/clearskies/input_requirements/__init__.py) that you can attach to columns like this:

```
from collections import OrderedDict
from clearskies import Model
from clearskies.column_types import string, email, integer, created, updated
from clearskies.input_requirements import required, maximum_length


class User(Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            string('name', input_requirements=[required(), maximum_length(255)]),
            email('email', input_requirements=[required(), maximum_length(255)]),
            integer('age'),
            created('created'),
            updated('updated'),
        ])
```

Currently only the following additional input requirements are available:

| Name           | Paramaters                  | Description                                                          |
|----------------|-----------------------------|----------------------------------------------------------------------|
| maximum_length | The maximum length to allow | Ensures that the user input does not exceed the maximum length       |
| minimum_length | The minimum length to allow | Ensures that the user input is at least as long as the minium length |
| required       | None                        | Ensures that user input is provided                                  |

**@IMPORTANT** These input requirements are only relevant for the automatic API endpoints generated by clearskies.  They are **not** enforced for any direct model changes made in your own code.  In other words, having the `name` column marked as required will stop an end user from creating a record without a name via API, but it will not stop a developer from doing this in a background process somewhere:

```
users.create({'email': 'bob@example.com'})
```

## Life Cycle

Columns have their own life cycle which is [very similar to that for models](./3_models.md#life-cycle):

| Method Name            | Lifecycle                                        | Return Value | Typical Usage                                                       |
|------------------------|--------------------------------------------------|--------------|---------------------------------------------------------------------|
| check_configuration    | Called when the column is first instantiated     | None         | Throw exceptions if column configuration is invalid                 |
| finalize_configuration | Called after checking the column configuration   | dictionary   | Make additional changes to the column configuration, if needed      |
| from_backend           | Transform data that is coming out of the backend | Any          | Convert raw backend data to a more flexible format when appropriate |
| pre_save               | Called before data is persisted to the backend   | dictionary   | Make desired transformations to the data before things are saved    |
| to_backend             | Called immediately before persisting data        | dictionary   | Exclude data from the save or make backend-specific transformations |
| post_save              | Called after data is persisted to the backend    | None         | Make additional changes that require the record id to happen        |
| pre_delete             | Called before the record is deleted              | None         | Perform any pre-deletion cleanup                                    |
| post_delete            | Called after the record is deleted               | None         | Delete any related records                                          |

## Custom Column Types

To show how you can use columns and lifecycles to generate your own custom logic, let's look at a simple example.  We will build a datetime column which will automatically set itself a specific amount of time before or after another datetime column.  You might use this to schedule a followup notice, schedule some background tasks, etc...  Here are some high level notes:

1. We need a configuration option so the developer can tell us what column to use for the "source" datetime.
2. We need a configuration option so the developer can specify how far in the future/past to set the new column
3. We want to check the configuration to make sure it makes sense
4. We only want to change the scheduled time when the "source" column changes
5. We always want to change the scehduled time when the "source" column changes
6. This column should be read-only (it will set itself automatically, so we don't need users to provide a value)

Let's call this column type `Scheduled`.  Let's start with a base column definition:

```
import clearskies


class Scheduled(clearskies.column_types.DateTime):
    @property
    def is_writeable(self):
        return False


def scheduled(name, **kwargs):
    return clearskies.column_types.build_column_config(name, Scheduled, **kwargs)
```


So we have a class named `Scheduled` that extends the `DateTime` class, is not writeable, and has the same builder function as the other column type classes.

Now let's tackle configuration: we want to accept two required configs: `source_column_name` and `timedelta`.  The former will be a string and the latter will be a dictionary which we will pass as kwargs to a `datetime.timedelta` object.  We'll add the following to our class definition:


```
import datetime


class Scheduled(clearskies.column_types.DateTime):
    # if we specify some config names here, the base `_check_configuration` method will
    # raise exceptions if the developer doesn't set them.
    required_configs = [
        'source_column_name',
        'timedelta',
    ]

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
```

Finally, we'll extend the `pre_save` hook and check the data dictionary to see if our source column is set.  If so, we'll take action!

```
    def pre_save(self, data, model):
        source_column_name = self.config('source_column_name')
        if source_column_name not in data:
            return data

        return {
            # always return the previous data first
            **data,

            # and then add on any new data
            self.name: data[source_column_name] + datetime.timedelta(**self.config('timedelta'))
        }
```

And that's it!  We would use this column in a model like so:

```
import clearskies
from .scheduled import scheduled


class Order(Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            clearskies.column_types.string('name'),
            clearskies.column_types.created('date_placed_at'),
            scheduled('send_feedback_request_at', source_column_name='date_placed_at', timedelta={'days': 30})
        ])
```

When an order object is created it will automatically store the current time in the `date_placed_at` column.  When the model sets the `date_placed_at` column, it will also set the `send_feedback_request_at` column to have a datetime 30 days in the future.  This will happen for all save operations of the model, regardless of whether the model is updated from an API endpoint, a scheduled task, or anything else.  Therefore, we have acheived all the goals we set out at the beginning. In particular, not only does the business logic for our `send_feedback_request_at` column automatically apply throughout the application, but it is easily reconfigured or re-used for other similar needs.  The logic is wrapped up in a column class which can be dropped into any model with a single line of code!

The final column class can be viewed [here](./Scheduled.py)

Next: [Handlers](5_handlers.md)
