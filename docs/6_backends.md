# Backends

The backend (i.e, the place where data is loaded from and persisted to) is very flexible in clearskies.  While clearskies defaults to using an SQL database, this can be changed from one model to another or overridden at run time.

The main "kinds" of backends currently available are the:

1. [Cursor Backend](#cursor-backend), which persists data to a MySQL/MariaDB database via [PyMySQL](https://pypi.org/project/PyMySQL/)
2. [Memory Backend](#memory-backend), which stores data locally.  This is useful for working with temporary data or when running test suites.
3. [API Backend](#api-backend), which is used to normalize API interactions as well as to automate integrations with APIs powered by clearskies

# Configure the Backend for a Model Class

Both the [model and models](./3_models.md) classes need a backend in order to function.  The base model and models classes expect the first parameter to be the backend for the model.  Therefore, you specify the backend for a model by having the desired one injected in the constructor of your model class, and then passing it along as the first parameter to the parent constructor.  Bringing this all together, a model class that uses the cursor backend would typically look like:

```
class MyModel(clearskies.Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)
```

The same thing needs to happen in the models class:

```
class MyModels(clearskies.Models):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)
```

# Cursor Backend

The cursor backend uses [PyMySQL](https://pypi.org/project/PyMySQL/) to connect to a database.  By default, it expects the database credentials to be present in environment variables or a `.env` file with the following names:

| Name        | Value                                        |
|-------------|----------------------------------------------|
| db_username | The username to connect to the database with |
| db_password | The password to connect to the database with |
| db_host     | The URL/IP address/host for the database     |
| db_database | The name of the database to use              |

The cursor backend is available from the dependency injection container by the name `cursor_backend`, so you would use that name to inject the cursor backend to a model and configure it to save data to a database:

```
class MyModel(clearskies.Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

class MyModels(clearskies.Models):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)
```

# Memory Backend

The memory backend is an in-memory datastore that comes with clearskies.  The most common use-case is for testing: you can configure clearskies to replace the cursor backend with the memory backend at run time, and your models will behave the same without having to worry about connecting to an actual database for all of your tests.

Of course, it can also be used as a temporary data store if desired.  Not surprisingly, the memory backend isn't a _perfect_ drop in replacement for an actual SQL database.  It supports the SQL features that clearskies uses by default: wheres, joins, groups, and sorts (although it doesn't support grouping yet).  The memory backend is available for injection under the `memory_backend` name, so if you wanted to configure a model to explicitly use the memory backend that would look like this:

```
class MyModel(clearskies.Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

class MyModels(clearskies.Models):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)
```

If your models use a cursor backend but you want to switch to a memory backend for testing, then you would specify this in your context:

```
# build our context
context = clearskies.contexts.cli(some_application)
# re-configure the `cursor_backend` name to point to the MemoryBackend class
context.bind('cursor_backend', clearskies.backends.MemoryBackend)
# and execute!
context()
```

The test context actually does this by default.

# API Backend

### Using the API Backend with other clearskies API endpoints

The API backend turns an API into an external data source from which you can read or write data.  This provides a different approach to API integration because it allows your code to interact with API endpoints just like it would data that comes out of a database.  This can be a big win for microservices where all APIs behave similarly - even more so when the APIs are backed by a clearskies RESTful API handler, which is what the API backend assumes by default.  Imagine for instance that a 3rd party is hosting an API endpoint that is defined like this:

```
from collections import OrderedDict
import clearskies
import clearskies_aws


class Widget(clearskies.Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            clearskies.column_types.string('name'),
            clearskies.column_types.string('description'),
            clearskies.column_types.integer('height'),
            clearskies.column_types.integer('width'),
            clearskies.column_types.integer('length'),
        ])

class Widgets(Models):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def model_class(self):
        return Widget


api = clearskies_aws.contexts.lambda_alb(
    {
        'handler_class': clearskies.handlers.RestfulAPI,
        'handler_config': {
            'models_class': Widgets,
            'readable_columns': ['name', 'description', 'height', 'width', 'length'],
            'searchable_columns': ['name', 'description', 'height', 'width', 'length'],
            'default_sort_column': 'name',
            'authentication': clearskies.authentication.secret_bearer(secret='SECRET_API_KEY'),
        },
    },
)

def lambda_handler(event, context):
    return api(event, context)
```

To summarize, this publishes a read-only API endpoint that requires a Bearer token (literally, `SECRET_API_KEY`) and which publishes name, description, and size information about widgets.  Imagine that this api endpoint is being hosted at `https://api.example.com/widgets/v1/` If we wanted to integrate with this API endpoint then we would build a similar model class that uses the API backend:

```
class Widget(clearskies.Model):
    def __init__(self, widget_api_backend, columns):
        super().__init__(widget_api_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            clearskies.column_types.string('name'),
            clearskies.column_types.integer('height'),
            clearskies.column_types.integer('width'),
            clearskies.column_types.integer('length'),
        ])

class Widgets(Models):
    def __init__(self, widget_api_backend, columns):
        super().__init__(widget_api_backend, columns)

    def model_class(self):
        return Widget
```

Note the two differences: we've dropped the description column (because we don't need it in our hypothetical integration, so we can ignore it) and our backend is now the `widget_api_backend`.  This backend doesn't exist yet, but it will tell clearskies how to connect to our desired API.  We can define it in our application or context dependency injection configuration:

```
import clearskies

application = clearskies.application(
    some_callable,
    bindings={
        'widget_api_backend': clearskies.BindingConfig(
            clearskies.backends.ApiBackend,
            url='https://api.example.com/widgets/v1/',
            auth=clearskies.authentication.secret_bearer(secret='SECRET_API_KEY'),
        )
    },
)

# OR

context = clearskies.contexts.cli(
    some_callable,
    bindings={
        'widget_api_backend': clearskies.BindingConfig(
            clearskies.backends.ApiBackend,
            url='https://api.example.com/widgets/v1/',
            auth=clearskies.authentication.secret_bearer(secret='SECRET_API_KEY'),
        )
    },
)
```

This tells the API backend what URL to use and how to authenticate to it.  If we wanted to, we could also just define this behavior in a class and attach to our dependency injection configuration:

```
import clearskies


class WidgetApiBackend(clearskies.backends.ApiBackend):
    def __init__(self, requests):
        super().__init__(requests)
        secret_bearer_auth = clearskies.authentication.SecretBearer()
        secret_bearer_auth.configure(secret='SECRET_API_KEY')
        self.configure(url='https://api.example.com/widgets/v1', auth=secret_bearer_auth)
```

The one advantage of this is that clearskies will automatically provide any imported classes for dependency injection under their snake-cased name (see [the documentation on dependency injection](./9_dependency_injection.md) for more information).

So what does this get us?  We can now use our widget model just like we would use a model that utilizes a cursor backend:

```
def my_callable(widgets):
    for widget in widgets.where('width>100').where('width<=200').sort_by('length', 'desc').limit(0, 50):
        print(widget.name)
```

Behind the scenes clearskies is building an API request to `https://api.example.com/widgets/v1/search` with the appropriate pagination, sort, and filtering parameters set to find the records we requested.  We're not limited to reading of course, and can create/update records as well (assuming those capabilities are enabled on the API endpoint):

```
def my_other_callable(widgets):
    widget = widgets.where('id=10').first()
    if not widget.exists:
        return 'Whoops, record doesn't exist'

    # make a new widget with double the size of the original
    new_widget = widgets.create({
        'name': 'Double size',
        'width': 2*widget.width,
        'length': 2*widget.length,
        'height': 2*widget.height,
    })
    print(new_widget.id)

    # and update the description of the original widget
    widget.save({'description': 'the smaller widget'})
```

### Swapping out the memory backend for testing

In addition, we can still swap out the API backend for the memory backend in tests, letting us do things like this:

```
# launch our callable in a test context
test_context = clearskies.contexts.test(my_callable)

# the test context always generates a memory backend, but it can only automatically replace the
# cursor backend.  As a result, we have to ask it to replace our api backend
test_context.bind('widget_api_backend', test_context.memory_backend)

# now let's go ahead and create a few records in the memory backend for our model class:
widgets = test_context.build(Widgets)
widgets.create({'name': 'will get returned last', 'width': 200, 'length': 400})
widgets.create({'name': 'will get returned first', 'width': 101, 'length': 500})
widgets.create({'name': 'will be ignored', 'width': 50, 'length': 200})
widgets.create({'name': 'also ignored', 'width': 201, 'length': 200})

# and run our test
test_context()
# which prints out:
"""
will get returned first
will get returned last
"""
```
### Working with non-clearskies APIs

Of course, the API backend can integrate with more than just clearskies API endpoints.  For other APIs you would extend the API backend directly and then build the integration logic for the API.  There are more details about this in the (TBW) docblock of API backend class.
