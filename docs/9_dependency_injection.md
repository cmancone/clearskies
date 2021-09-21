# Dependency Injection

The dependency injection system from clearskies is a name-based system, rather than type-based system.  This is partly because types will always be optional in Python, and partly because early versions of clearskies used [pinject](https://github.com/google/pinject), which is a name-based injection system.

Dependency injection settings can be configured at both the application and context level.  This allows you to set defaults for an application and then override them if necessary at run time.  In addition, there are a variety of ways to configure dependency injection, with a clear order priority to resolve conflicts.  Finally, clearskies can auto-load all the classes in your application to make dependency injection configuration as automated as possible.

There is a lot to unpack, so this is broken into a number of sections:

1. [Name Based Injection](#name-based-injection)
2. [Configuring Dependency Injection](#configuring-dependency-injection)
3. [Standard Dependencies](#standard-dependencies)
4. [Configuring Dependencies](#configuring-dependencies)
5. [Example Uses](#example-uses)

## Name Based Injection

Name-based injection means that when clearskies is deciding what to inject for a function/contructor parameter, it looks at the actual parameter name rather than the parameter type.  Consider the following code:

```
import clearskies

def my_function(input_output, requests, now):
    print(input_output)
    print(requests)
    print(now)

cli_callable = clearskies.contexts.cli(my_function)
if __name__ == '__main__':
    cli_callable()
```

Since `my_function` is being executed by the clearskies context, clearskies provides all of its parameters via the dependency injection configuration.  This means that clearskies will check the dependency injection configuration for parameters named `requests`, `now`, and `input_output`.  In this example we haven't configured anything for our dependency injection container, but it just so happens that these are [standard dependencies](#standard-dependencies) that are always provided by clearskies.  If we run it, we'll get back something like this:

```
<clearskies.input_outputs.cli.CLI object at 0x7f66c23ba340>
<requests.sessions.Session object at 0x7f66c13d6580>
2021-09-18 13:27:45.904158
```

## Configuring Dependency Injection

There are a number of ways to configure the dependency injection container.  In order of priority (highest priority items first):

1. ["di"](#1-di)
2. [Directly Binding Values](#2-directly-binding-values)
3. [Add Classes and Modules](#3-add-classes-and-modules)
4. [Additional Configuration Classes](#4-additional-configuration-classes)
5. [Base Dependencies](#5-base-dependencies)

### 1. di

The name `di` is the only reserved keyword in the clearskies dependency injection system.  If you ask for a dependency with this name, clearskies will inject the current dependency injection container:

```
import clearskies

def my_function(di):
    print(di)

cli_callable = clearskies.contexts.cli(my_function)
if __name__ == '__main__':
    cli_callable()
```

Which would give you:

```
<clearskies.di.standard_dependencies.StandardDependencies object at 0x7ff642c0fca0>
```

Which is an instance of the [StandardDependencies class](../src/clearskies/di/standard_dependencies.py).

### 2. Directly Binding Values

The dependency injection container has a `bind` method that takes a name and value.  The contexts also have `bind` methods which pass calls along to the depenency injection container.  Finally, when building contexts or applications you can provide the `bindings` kwarg to pass a dictionary of bindings along into the dependency injection container.  This can include either "final" values or classes.  Keep in mind though that a later invocation of `bind` can override previous values:

```
import clearskies

class MyAwesomeClass:
    def __init__(self, some_other_value):
        self.some_other_value = some_other_value

    def print_my_value(self):
        print(self.some_other_value)

def my_function(my_favorite_number, my_favorite_letter, my_awesome_class):
    print(my_favorite_number)
    print(my_favorite_letter)
    my_awesome_class.print_my_value()

my_application = clearskies.Application(
    clearskies.handlers.Callable,
    {'callable': my_function},
    bindings={
        'my_awesome_class': MyAwesomeClass,
        'some_other_value': 'foo',
    },
)

cli_callable = clearskies.contexts.cli(
    my_application,
    bindings={
        'my_favorite_number': 5,
        'my_favorite_letter': 'A',
    },
)
cli_callable.bind('some_other_value', 'bar')
if __name__ == '__main__':
    cli_callable()
```

And if you ran this you would get:

```
5
A
bar
```

### 3. Add Classes and Modules

The dependency injection container has a method called `add_classes` that you can use to register additional classes for dependency injection.  When using it to register classes, you don't provide the name to inject it under.  Instead, clearskies just converts the class names to snake_case and automatically registers them with that name.

`add_modules` allows you to provide modules to inject.  However, it doesn't let you literally inject the modules.  Instead, it finds all classes in the modules and registers them with `add_classes`.

Both of these methods are exposed to the application and context via the `binding_classes` and `binding_modules` kwargs which accept a list of classes or modules:

```
import clearskies

class MyFirstClass:
    class_number = 1

class MySecondClass:
    class_number = 2

def my_function(my_first_class, my_second_class):
    print(my_first_class.class_number)
    print(my_second_class.class_number)

my_application = clearskies.Application(
    clearskies.handlers.Callable,
    {'callable': my_function},
    binding_classes=[MyFirstClass],
)

cli_callable = clearskies.contexts.cli(
    my_application,
    binding_classes=[MySecondClass],
)
if __name__ == '__main__':
    cli_callable()
```

Which prints:

```
1
2
```

**HOWEVER**, you probably don't have to do this.  By default clearskies will automatically find any classes that are defined in the current script or which are defined in a module in the current directory or a subdirectory of the current directory, and import those, so actually this works exactly the same as the previous example:

```
import clearskies

class MyFirstClass:
    class_number = 1

class MySecondClass:
    class_number = 2

def my_function(my_first_class, my_second_class):
    print(my_first_class.class_number)
    print(my_second_class.class_number)

cli_callable = clearskies.contexts.cli(my_function)
if __name__ == '__main__':
    cli_callable()
```

### 4. Additional Configuration Classes

The dependency injection container allows you to provide additional classes that extend the `clearskies.di.AdditionalConfig` class and then define dependencies by declaring methods named `provide_[name]`, where `[name]` is the dependency name.  clearskies will call the appropriate method when it is needed, as well as provide any parameters needed by the method.

You can specify these classes via the `add_additional_configs` method on the dependency injection container, which is exposed via the `additional_configs` kwarg when building a context or an application.  This kwarg accepts a list such classes, or an instance of such a class.

```
import clearskies

class MultiplyThem(clearskies.di.AdditionalConfig):
    def __init__(self, first_number):
        self.first_number = first_number

    def provide_multiplied_value(self, second_number):
        return self.first_number*second_number

def my_function(multiplied_value):
    print(multiplied_value)

cli_callable = clearskies.contexts.cli(
    my_function,
    bindings={'first_number': 2, 'second_number': 4},
    additional_configs=[MultiplyThem],
)
if __name__ == '__main__':
    cli_callable()
```

Which prints:

```
8
```

### 5. Base Dependencies

Finally, the dependency injection container has a base class that can provide "default" dependencies.  clearskies uses the [StandardDependencies](../src/clearsies/di/standard_dependencies.py) for this, but you can override the class to use in your application or context.  This class must extend the `clearskies.di.DI` class, but you should probably extend `clearskies.di.StandardDependencies` so you'll have the same defaults as clearskies itself.  The class specifies default dependencies by declaring `provide_[name]` functions, just like the [additional configuration classes do](#additional-configuration-classes).  The base DI class can be changed in either the application or context by setting the `di_class` kwarg:

```
import clearskies

class MyDefaultDependencies(clearskies.di.StandardDependencies):
    def provide_some_value(self):
        return 'hey'

def my_function(some_value):
    print(some_value)

# you can set it here
my_application = clearskies.Application(
    clearskies.handlers.Callable,
    {'callable': my_function},
    di_class=MyDefaultDependencies,
)

# or here
cli_callable = clearskies.contexts.cli(
    my_application,
    di_class=MyDefaultDependencies,
)
if __name__ == '__main__':
    cli_callable()
```

which prints:

```
hey
```

## Standard Dependencies

The following standard dependencies are defined in the [StandardDependencies](../src/clearskies/di/standard_dependencies.py) class and are therefore accessible without additional configuration:

| Injection Name         | Value                                                                                                                                 |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| `columns`              | A clearskies [Columns](../src/clearskies/columns.py) object                                                                           |
| `cursor`               | A PyMYSQL cursor object                                                                                                               |
| `cursor_backend`       | The [cursor backend](./6_backends.md#cursor-backend)                                                                                  |
| `environment`          | A clearskies [Environment](../src/clearskies/environment.py) object                                                                   |
| `input_output`         | A clearskies InputOutput object (the exact class depends on the context)                                                              |
| `jose_jwt`             | The Jose JWT module (e.g. `from jose import jwt`)                                                                                     |
| `memory_backend`       | The [memory backend](./6_backends.md#memory-backend)                                                                                  |
| `now`                  | A datetime object set to the current time                                                                                             |
| `oai3_schema_resolver` | A clearskies [OAI3 Schema Resolver](../src/clearskies/autodoc/formats/oai3_json/oai3_schema_resolver.py) - used for autodocumentation |
| `requests`             | A requests object set with an exponential backoff/retry strategy                                                                      |
| `secrets`              | The secret manager (but requires configuration)                                                                                       |
| `sys`                  | The standard Python `sys` module                                                                                                      |

## Configuring Dependencies

In addition to confguring the dependency injection container, clearskies also supports configuring the dependencies themselves.  This is frequently used to add flexibility to core classes.  For instance, a class used to integrate with a third party service may accept some simple configuration parameters to control whether it pulls an API key out of the environment or a secret manager.  You configure a dependency by creating an instance of the [BindingConfig class](../src/clearskies/binding_config.py), which carries information about the dependency and its configuration.  You can then [bind](#2-directly-binding-values) the BindingConfig object to an application or context.  The actual configuration happens via a `configure` method which clearskies expects the dependency to have.  When clearskies builds an instance of the class, it will call this method and pass in the configuration.

Here is an example of such a configurable class:

```
class ApiService:
    def __init__(self, requets, environment, secrets):
        self.requests = requests
        self.secrets = secrets
        self.environment = environment

    def configure(self, key_from_environment=None, key_from_secrets=None):
        if key_from_environment is None and key_from_secrets is None:
            raise ValueError("You must configure the MyConfigurableDepedency class to specify a key name in either the environment or secret manager")
        if key_from_environment is not None and key_from_secrets is not None:
            raise ValueError("Both key_from_environment and key_from_secrets were set, but only one should be")
        if key_from_environment:
            self.api_key = self.environment.get(key_from_environment)
        else:
            self.api_key = self.secrets.get(key_from_secrets)

    def do_something(self):
        # do something with our API key
        self.requests.get('https://www.example.com', headers={'Authorization': f'Bearer {sefl.api_key}'})
```

And you could use it like this:

```
import clearskies

def my_function(api_service):
    api_service.do_something()

# As always, you can set this at the application level
my_application = clearskies.Application(
    clearskies.handlers.Callable,
    {'callable': my_function},
    bindings={'api_service', clearskies.BindingConfig(ApiService, key_from_environment='MY_API_KEY')},
)

# or at the context.  If set in both places, the context overrides the application
cli_callable = clearskies.contexts.cli(
    my_application,
    bindings={'api_service': clearskies.BindingConfig(ApiService, key_from_secrets='/path/from/secret/manager')},
)
if __name__ == '__main__':
    cli_callable()
```

## Example Uses

This variety of dependency injection configuration options gives clearskies the flexibility it needs to match a wide variety of use-cases and operational modes.  To help give a concrete picture of how these things work, here are some examples of mixing and matching these options to streamline application development and maintenance:

**Switching DB connection method:** Perhaps most of your production workloads use a "standard" database connection by grabbing username/password/host/database out of environment keys.  However, some workloads grab [temporary credentials from a dynamic secret producer](https://docs.akeyless.io/docs/create-dynamic-secret-to-sql-db).  The exact producer used varies depending on the level of access the application needs.  Developers also use temporary credentials but have to connect through a bastion host.  In this case, the "standard" dependency injection configuration will work for most of your production workloads.  For workloads that use temporary credentials, you can create an [additional configuration class](#4-additional-configuration-classes) that replaces the standard database connection process (by declaring a `provide_cursor` method).  It fetches temporary credentials from a dynamic producer with a name that can be specified via [dependency configuration](#configuring-dependencies) and which depends on the configured environment.  This is configured in the applications that need the dynamic credentials.  However, you also need to support developers who connect through a bastion!  Since they will execute the application differently (i.e., they use a different context), you override the database connection method again in the context that developers will execute.  In this case, you switch it out for a different configuration class which similarly accepts the name of the dynamic producer to use, but also requires the hostname of the bastion host.  It will then connect through the bastion, fetch temporary credentials, and connect to the database.  All by just switching out a single line of code depending on the context.

Next: [Testing](./10_testing.md)
