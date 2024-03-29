# Models

1. [Model Classes](#model-classes)
    1. [Overview](#model-overview)
    2. [Example and Usage](#example-and-usage)
    3. [Lifecycle Hooks](#lifecycle-hooks)
2. [Query Builder](#query-builder)
    1. [Overview](#query-builder-overview)

## Model Classes

### Model Overview

clearskies makes use of fairly standard models.  As in other python frameworks, a schema is declared in the model class.  This schema is then used throughout clearskies in order to automate a number of common tasks (input validation, transforming data during the save process, building API endpoints, autodocumentation, etc...).

Dependencies are passed in via the model constructor.  To work, models need to at least receive a proper backend as well as the the [columns](../src/clearskies/columns.py) object.  You can add more dependencies as needed, of course.

Most of your models will probably use the `cursor_backend`.  This means that the model will save/load data from an SQL database using the [pymysql library](https://pypi.org/project/PyMySQL/), with the table name determined by calling `model.table_name`.  Unless you override this property, clearskies will "pluralize" the model class name, convert to snake case, and use it as the table name (e.g. `UserOrders` -> `user_orders`).

All models are assumed to have a column named `id` which is an auto-incrementing integer.  This is automatically added to your column definitions, even if you don't specify it yourself.  You cannot remove this column (report an issue if that is a problem for you), but if you need a different column type you can do that by explicitly declaring the `id` column in your columns definition.

### Example and Usage

Bringing it all together, a simple model class looks like this:

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
            string('name'),
            email('email'),
            integer('age'),
            created('created'),
            updated('updated'),
        ])
```

These operate about as you would expect:

```
if user.exists:
    print('This user object has a record loaded from the backend')
if not another_user.exists:
    print('This user object does not')

print(user.id)
print(user.email)

user.save({'name': 'A new name', 'email': 'someone@example.com'})
```

### Lifecycle Hooks

Model classes have a number of lifecycle hooks to give fine-grained control over save behavior.  The following table gives the name of the method you would extend to use a lifecycle hook, as well as when it is called and typical usage:

| Method Name | Lifecycle                                      | Return Value | Typical Usage                                                       |
|-------------|------------------------------------------------|--------------|---------------------------------------------------------------------|
| pre_save    | Called before data is persisted to the backend | dictionary   | Make desired transformations to the data before things are saved    |
| to_backend  | Called immediately before persisting data      | dictionary   | Exclude data from the save or make backend-specific transformations |
| post_save   | Called after data is persisted to the backend  | None         | Make additional changes that require the record id to happen        |
| pre_delete  | Called before the record is deleted            | None         | Perform any pre-deletion cleanup                                    |
| post_delete | Called after the record is deleted             | None         | Delete any related records                                          |

In addition there are 4 methods you can call to query metadata about the save process:

| Method Name    | Parameters        | Availability | Usage                                                                        |
|----------------|-------------------|--------------|------------------------------------------------------------------------------|
| is_changing    | column_name, data | During Save  | Returns True/False to denote if the given column is changing during the save |
| latest         | column_name, data | During Save  | Returns the new data if the column is changing, or the old data if not       |
| was_changed    | column_name       | After Save   | Returns True/False to denote if the column was changed during the last save  |
| previous_value | column_name       | After Save   | Returns the data for the column from before the previous save                |

The difference between `pre_save` and `to_backend` is subtle but important.  If you make changes to the data in `pre_save`, those changes will be reflected everywhere: both in the data persisted to the backend and then also in the data passed to `post_save`.  In contrast, `to_backend` only affects the data which is persisted to the backend.  A common use-case for this is to exclude data from the save.  For instance, you may want to accept user input to control behavior in pre/post save, but don't can't persist it to the backend because it doesn't have a corresponding column in the database.  In that case, you can use `to_backend` to remove it from being saved to the backend.  You can also use it to make necessary transformations when saving to the backend.


```
import datetime
import clearskies

class LifeCycleExample(clearskies.Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            clearskies.column_types.string('name'),
            clearskies.column_types.datetime('updated'),
        ])

    def pre_save(self, data):
        print('pre_save invoked!')

        return {
            # First, make sure and return the old stuff! If you remove anything from the returned dictionary,
            # then clearskies will simply forget that data and not save it.
            **data,

            # then let's also keep track of when the record is saved.  This is just for example purposes,
            # you wouldn't actually want to do this with a lifecycle hook because the clearskies.column_types.updated
            # column type already does exactly this.
            'updated': datetime.datetime.now(),
        }

    def to_backend(self, data, columns):
        print('to_backend invoked!')

        # remove `send_email` if it is present because it doesn't have a corresponding column in
        # the database, so if we don't remove it we will get an SQL error.
        if 'send_email' in data:
            del data['send_email']

        return {
            **data,

            # of course, we can't save a datetime object to the database, so we need to stringify it.
            # Again, the clearskies.column_types.upated column already does this, so this is just an example.
            'updated': data['updated'].strftime('%Y-%m-%d')
        }

    def post_save(self, data, id):
        print('post_save invoked!')

        # data['updated'] exists here and is still a datetime object, because changes made in `to_backend`
        # are only reflected in the backend - not in `post_save`.  Also, since our pre_save hook *always*
        # adds in the 'updated' key, we can count on data['updated'] always existing here, even if it
        # wasn't originally part of the save data.
        print(data['updated'].year)

        if self.is_changing('name', data):
            # self.latest is just a convenient shorthand to get either the new value
            # (out of the data object) or the old value (out of self.data) depending on whether or not
            # the value is changing in the save data.  This is redundant in this case though,
            # because we already used is_changing to decide that data['name'] is changing, which
            # means that the 'name' key exists in data.  Therefore, self.latest('name', data)
            # will just return data['name'], since that is the latest value!
            print('Name is changing to ' + self.latest('name', data))

        # data is just a dictionary, so we use data.get('send_email') as a quick shorthand
        # to check if send_email both exists in data and has a truthy value.
        if data.get('send_email'):
            print('Sending email to user!')
```

If you then used that model:

```
lifecycle_example = LifeCycleExample(cursor_backend, columns)
lifecycle_example.data = {'name': 'test', 'id': 5}

print(lifecycle_example.data)

lifecycle_example.save({'name': 'awesome!', 'send_email': True})

print(lifecycle_example.data)
```

It would print:

```
{'name': 'test', 'id': 5}
pre_save invoked!
to_backend invoked!
post_save invoked!
2021
Name is changing to awesome!
sending email to user!
{'name': 'awesome!', 'id': 5, 'updated': <datetime.datetime object>}
```
## Query Builder

The model classes in clearskies also serve as a query builder, which looks a little like this:

```
start = 0
limit = 100
users = User(backend, cursor)
for user in users.where("age>20").sort_by('name', 'desc').limit(start, limit):
    print(user.email)

for user in users.where("name in ('bob', 'alice')"):
    user.delete()

new_user = users.create({'name': 'bob', 'email': 'bob@example.com', 'age': 25})

# or...
new_user = users.empty_model()
new_user.save({'name': 'bob', 'email': 'bob@example.com', 'age': 25})

# find() only returns the first record, which will be empty if the record does not exist
first_record = users.find('id=1')
if first_record.exists:
    print('Found it!')
else:
    # model properties are None for a non-existent record
    print(first_record.name == None)

# chaining `where` clauses together combines with AND
matching_users = users.where("age>20").where("age<50").where("name LIKE '%greg%'")
```

The `where` method is worth a mention.  Despite appearances, you aren't actually building SQL.  Indeed, clearskies is designed so that backends are completely flexible - a model may be attached to an im-memory store, an API, a DynamoDB Table, etc...  The clearskies query builder uses SQL-like input because this is often more intuitive then having to learn yet-another SDK interface.  Most importantly, you can safely inject raw user input here.  Therefore, `where` accepts a string with the format `[COLUMN_NAME] [OPERATOR] [VALUE]`.  The list of allowed operators is defined [at the top of this class](../src/clearskies/condition_parser.py).

The models class also has methods for `join` and `group_by`.  Note that these methods may not work in all backends.

Next: [Columns](./4_columns.md)
