# Models and Columns

1. [Model Classes](#model-classes)
    1. [Overview](#overview)
    2. [Example and Usage](#example-and-usage)
    3. [Lifecycle Hooks](#lifecycle-hooks)
2. [Models Classes](#models-classes)
3. [Column Classes](#column-classes)

## Model Classes

### Overview

clearskies makes use of fairly standard models.  As in other python frameworks, a schema is declared in the model class.  This schema is then used throughout clearskies in order to automate a number of common tasks (input validation, transforming data during the save process, building API endpoints, autodocumentation, etc...).

Dependencies are passed in via the model constructor.  To work, models need to at least receive a proper backend as well as the the [columns](../src/clearskies/columns.py) object.  You can add more dependencies as needed, of course.

Most of your models will probably use the `cursor_backend`.  This means that the model will save/load data from an SQL database using the `pymysql` library, with the table name determined by calling `model.table_name`.  Unless you override this property, clearskies will "pluralize" the model class name, make it all lower case, and use it as the table name (e.g. User -> users).

An OrderedDict is used for the columns definition to allow clearskies to order results in the JSON response of API endpoints, in the auto generated documentation, and other places as appropriate.

All models are assumed to have a column named `id` which is an auto-incrementing integer.  This is automatically added to your column definitions, even if you don't specify it yourself.  You cannot remove this column (file an issue if that is a problem for you), but if you need a different column type you can do that by explicitly declaring the `id` column in your columns definition.

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

Model classes have a number of lifecycle hooks to give fine-grain control over save behavior.  This is typically where your business logic lives.  The following table gives the name of the method you would extend to use a lifecycle hook, as well as when it is called and usage:

| Method Name | Lifecycle                                      | Return Value | Typical Usage                                                    |
|-------------|------------------------------------------------|--------------|------------------------------------------------------------------|
| pre_save    | Called before data is persisted to the backend | dictionary   | Make desired transformations to the data before things are saved |
| post_save   | Called after data is persisted to the backend  | dictionary   | Make additional changes that require the record id to happen     |
| pre_delete  | Called before the record is deleted            | None         | Perform any pre-deletion cleanup                                 |
| post_delete | Called after the record is deleted             | None         | Delete any related records                                       |

Here are the actual method definitions that you would declare in your model class:

```
class ModelClass(clearskies.Model):
    def pre_save(self, data):
        return data

    def post_save(self, data, id):
        return data

    def pre_delete(self):
        pass

    def post_delete(self):
        pass
```

Note that inside pre/post save you can differentiate between a create and an update operation by checking the value of `self.exists`.  If your business logic requires information about the record id, then you will want to use `post_save`.  `pre_save` is not passed the model id because it is called before data is persisted to the backend, and at this point in time there will not be an id during a create operation (although for an update you could use `self.id` inside `pre_save` to tell what the record id is).

The `data` dictionary passed into `pre_save` and `post_save` is the data passed in to the `.save` operation.  As a result, this is *not* guaranteed to include entries for every column in the model.  In addition, the internal model state is only updated after the save/delete has completely finished.  This means that if you fetch data out of your model in the lifecycle hooks, it will reflect the pre-save data: *not* the data being saved in the current operation.  If you need to know what data is being saved, you can just fetch it out of the dictionary.  If a particular column is not present in the data dictionary, then that column is not being set as part of the current create/update operation.
